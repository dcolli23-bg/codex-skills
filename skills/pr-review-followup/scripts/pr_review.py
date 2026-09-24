#!/usr/bin/env python3
"""Collect complete PR feedback and post explicitly reviewed reply plans."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


class AuditError(Exception):
    """A completeness or posting-safety condition could not be established."""


def now():
    return datetime.now(timezone.utc).isoformat()


def decode(text):
    try:
        value = json.loads(text)
    except (ValueError, UnicodeError) as exc:
        raise AuditError("Invalid/partial JSON; obtain a complete download.") from exc
    if isinstance(value, dict) and any(
        value.get(key) for key in ("bodyTruncated", "truncated", "isTruncated")
    ):
        raise AuditError("Truncated response; obtain a complete download.")
    return value


def run(command, body=None):
    result = subprocess.run(
        command, input=body, capture_output=True, text=True, timeout=150
    )
    if result.returncode:
        raise AuditError(result.stderr.strip() or result.stdout.strip() or "CLI failed")
    return result.stdout


class Client:
    """Reuse existing CLI authentication; never read provider credentials."""

    def __init__(self, args):
        self.args = args
        if args.transport == "bga" and not args.connection_id:
            raise AuditError("BGA requires a discovered --connection-id.")

    def get(self, path, page=None):
        if self.args.transport == "gh":
            endpoint = path + (f"?per_page=100&page={page}" if page else "")
            return decode(run(["gh", "api", "--method", "GET", endpoint]))
        with tempfile.TemporaryDirectory(prefix="pr-review-download-") as temp:
            output = Path(temp) / "body.json"
            command = [
                str(self.args.bga_cli.expanduser()), "download",
                self.args.connection_id, "--method", "GET", "--path", path,
                "--output", str(output),
            ]
            if page:
                command += ["--query", "per_page=100", "--query", f"page={page}"]
            run(command)
            return decode(output.read_text(encoding="utf-8"))

    def post(self, path, payload):
        body = json.dumps(payload)
        if self.args.transport == "gh":
            return decode(run(
                ["gh", "api", "--method", "POST", path, "--input", "-"], body
            ))
        envelope = decode(run([
            str(self.args.bga_cli.expanduser()), "call", self.args.connection_id,
            "--method", "POST", "--path", path,
            "--header", "Content-Type: application/json", "--body-text", body,
        ]))
        if not isinstance(envelope, dict) or envelope.get("status") != 201:
            raise AuditError("POST did not return confirmed creation; inspect remotely.")
        return decode(envelope.get("bodyText", ""))


def validate_identity(repo, pr):
    component = r"[A-Za-z0-9_][A-Za-z0-9_.-]*"
    if not isinstance(repo, str) or not re.fullmatch(
        rf"{component}/{component}", repo
    ):
        raise AuditError("Repository must be OWNER/REPO.")
    if type(pr) is not int or pr < 1:
        raise AuditError("PR number must be a positive integer.")


def head_of(metadata):
    try:
        sha = metadata["head"]["sha"]
    except (KeyError, TypeError) as exc:
        raise AuditError("PR metadata has no head SHA.") from exc
    if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40,64}", sha):
        raise AuditError("Invalid PR head SHA.")
    return sha


def save(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write("\n")


def paginate(client, path, label, pages_dir=None):
    records = []
    seen = set()
    for page in range(1, 1001):
        batch = client.get(path, page=page)
        if not isinstance(batch, list):
            raise AuditError(f"{label}: expected a complete JSON array.")
        if pages_dir:
            save(pages_dir / f"{label}-{page:04}.json", batch)
        for record in batch:
            if (
                not isinstance(record, dict)
                or type(record.get("id")) is not int
                or not isinstance(record.get("body"), str)
            ):
                raise AuditError(f"{label}: missing comment/review ID or complete body.")
            if record["id"] in seen:
                raise AuditError(f"{label}: repeated ID; pagination changed or repeated.")
            seen.add(record["id"])
        records.extend(batch)
        if len(batch) < 100:
            return records
    raise AuditError(f"{label}: pagination limit reached; collection is incomplete.")


def collect(client, repo, pr, out=None):
    validate_identity(repo, pr)
    base = f"/repos/{repo}"
    pr_path = f"{base}/pulls/{pr}"
    pages_dir = None
    if out:
        out.mkdir(parents=True, exist_ok=False)
        pages_dir = out / "pages"
        pages_dir.mkdir()
    metadata = client.get(pr_path)
    sha = head_of(metadata)
    if pages_dir:
        save(pages_dir / "pr-before.json", metadata)
    collections = {
        "inline": f"{pr_path}/comments",
        "issues": f"{base}/issues/{pr}/comments",
        "reviews": f"{pr_path}/reviews",
    }
    data = {
        name: paginate(client, path, name, pages_dir)
        for name, path in collections.items()
    }
    after = client.get(pr_path)
    if pages_dir:
        save(pages_dir / "pr-after.json", after)
    if head_of(after) != sha:
        raise AuditError("PR head moved during collection; recollect and reassess.")
    threads = {}
    for comment in data["inline"]:
        root_id = comment.get("in_reply_to_id") or comment["id"]
        threads.setdefault(root_id, []).append(comment["id"])
    snapshot = {
        "repo": repo, "pr": pr, "head_sha": sha, "collected_at": now(),
        "complete": True, "metadata": after, **data,
        "counts": {name: len(records) for name, records in data.items()},
        "threads": [
            {"root_id": root, "comment_ids": ids, "resolution_state": "unknown"}
            for root, ids in threads.items()
        ],
    }
    if out:
        save(out / "snapshot.json", snapshot)
    return snapshot


def validate_plan(plan, prefix):
    if not isinstance(plan, dict):
        raise AuditError("Plan must be a JSON object.")
    validate_identity(plan.get("repo"), plan.get("pr"))
    head_of({"head": {"sha": plan.get("head_sha")}})
    if not isinstance(plan.get("replies"), list):
        raise AuditError("Plan must contain a replies array.")
    if not prefix:
        raise AuditError("Reply prefix must not be empty.")
    seen = set()
    for reply in plan["replies"]:
        if not isinstance(reply, dict) or reply.get("kind") not in ("inline", "issue"):
            raise AuditError("Each reply must be inline or issue.")
        body = reply.get("body")
        if not isinstance(body, str) or not body.startswith(prefix):
            raise AuditError(f"Every reply must begin with {prefix!r}.")
        if not body[len(prefix):].strip():
            raise AuditError("Reply must contain an explanation after its prefix.")
        evidence = reply.get("evidence")
        if not isinstance(evidence, list) or not evidence or not all(
            isinstance(item, str) and item.strip() for item in evidence
        ):
            raise AuditError("Each reply needs a nonempty list of evidence strings.")
        if reply["kind"] == "inline":
            if type(reply.get("in_reply_to")) is not int or reply["in_reply_to"] < 1:
                raise AuditError("Inline replies need a root comment ID.")
        elif "in_reply_to" in reply:
            raise AuditError("Issue comments do not accept inline reply targets.")
        key = operation_key(plan, reply)
        if key in seen:
            raise AuditError("Duplicate reply in the plan.")
        seen.add(key)


def operation_key(plan, reply):
    identity = [
        plan["repo"].lower(), plan["pr"], reply["kind"],
        reply.get("in_reply_to"), reply["body"].strip(),
    ]
    return hashlib.sha256(json.dumps(identity).encode()).hexdigest()


def remote_match(snapshot, reply):
    records = snapshot["inline" if reply["kind"] == "inline" else "issues"]
    for comment in records:
        if (
            comment["body"].strip() == reply["body"].strip()
            and (
                reply["kind"] == "issue"
                or comment.get("in_reply_to_id") == reply["in_reply_to"]
            )
        ):
            return comment
    return None


@contextmanager
def receipt_file(path, apply):
    if not apply:
        yield None, path.read_text(encoding="utf-8") if path.exists() else ""
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        stream.seek(0)
        yield stream, stream.read()


def record(stream, event):
    if stream:
        stream.write(json.dumps({**event, "time": now()}) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def post_plan(client, plan, receipts, apply=False, prefix="[codex]"):
    validate_plan(plan, prefix)
    repo, pr = plan["repo"], plan["pr"]
    pr_path = f"/repos/{repo}/pulls/{pr}"
    results = []
    with receipt_file(receipts, apply) as (stream, previous_text):
        previous = {}
        for line in previous_text.splitlines():
            event = decode(line)
            if (
                not isinstance(event, dict)
                or event.get("state") not in ("pending", "confirmed")
                or not isinstance(event.get("key"), str)
            ):
                raise AuditError("Malformed receipt; inspect it before posting.")
            previous[event["key"]] = event
        snapshot = collect(client, repo, pr)
        if snapshot["head_sha"] != plan["head_sha"]:
            raise AuditError("PR head differs from audited plan; reassess before posting.")
        roots = {
            comment["id"] for comment in snapshot["inline"]
            if not comment.get("in_reply_to_id")
        }
        # Validate every target before making any write.
        for reply in plan["replies"]:
            if reply["kind"] == "inline" and reply["in_reply_to"] not in roots:
                raise AuditError("Inline target is not a root comment in this PR.")
            key = operation_key(plan, reply)
            if key in previous and not remote_match(snapshot, reply):
                raise AuditError(
                    "Prior receipt has no matching remote comment. Inspect remotely; "
                    "do not automatically retry an uncertain/deleted post."
                )
        for reply in plan["replies"]:
            key = operation_key(plan, reply)
            match = remote_match(snapshot, reply)
            if match:
                record(stream, {
                    "key": key, "state": "confirmed", "id": match["id"],
                    "repo": repo, "pr": pr, "reply": reply, "recovered": True,
                    "url": match.get("html_url"),
                })
                results.append({"action": "skip-existing", "id": match["id"]})
                continue
            if not apply:
                results.append({"action": "would-post", **reply})
                continue
            if head_of(client.get(pr_path)) != plan["head_sha"]:
                raise AuditError("PR head moved; stopped before the next write.")
            event = {"key": key, "repo": repo, "pr": pr, "reply": reply}
            record(stream, {**event, "state": "pending"})
            payload = {"body": reply["body"]}
            if reply["kind"] == "inline":
                path = f"{pr_path}/comments"
                payload["in_reply_to"] = reply["in_reply_to"]
            else:
                path = f"/repos/{repo}/issues/{pr}/comments"
            # Never retry this write automatically, including malformed responses.
            created = client.post(path, payload)
            if (
                not isinstance(created, dict)
                or type(created.get("id")) is not int
                or created.get("body") != reply["body"]
                or (
                    reply["kind"] == "inline"
                    and created.get("in_reply_to_id") != reply["in_reply_to"]
                )
            ):
                raise AuditError("Unverified POST response; inspect remote before retrying.")
            record(stream, {
                **event, "state": "confirmed", "id": created["id"],
                "url": created.get("html_url"),
            })
            snapshot["inline" if reply["kind"] == "inline" else "issues"].append(created)
            results.append({"action": "posted", "id": created["id"]})
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    fetch = commands.add_parser("collect", help="Download all feedback without posting")
    fetch.add_argument("--repo", required=True)
    fetch.add_argument("--pr", type=int, required=True)
    fetch.add_argument("--out", type=Path, required=True)
    post = commands.add_parser("post", help="Preview a plan; requires --apply to post")
    post.add_argument("--plan", type=Path, required=True)
    post.add_argument("--receipts", type=Path, required=True)
    post.add_argument("--prefix", default="[codex]")
    post.add_argument("--apply", action="store_true")
    for command in (fetch, post):
        command.add_argument("--transport", choices=("gh", "bga"), default="gh")
        command.add_argument("--connection-id")
        command.add_argument(
            "--bga-cli", type=Path,
            default=Path("~/.codex/skills/bga-connections/bga-connections"),
        )
    args = parser.parse_args()
    try:
        client = Client(args)
        if args.command == "collect":
            snapshot = collect(client, args.repo, args.pr, args.out)
            result = {
                "snapshot": str(args.out / "snapshot.json"),
                "head_sha": snapshot["head_sha"], "counts": snapshot["counts"],
                "complete": snapshot["complete"],
            }
        else:
            result = post_plan(
                client, decode(args.plan.read_text(encoding="utf-8")), args.receipts,
                args.apply, args.prefix,
            )
        print(json.dumps(result, indent=2))
    except (AuditError, OSError, subprocess.SubprocessError) as exc:
        print(f"Stopped: {exc}", file=sys.stderr)
        print("Do not blindly retry writes; inspect remote comments and receipts.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
