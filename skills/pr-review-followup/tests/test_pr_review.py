"""Offline checks for completeness and externally visible posting behavior."""

import argparse
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "pr_review.py"
SPEC = importlib.util.spec_from_file_location("pr_review", SCRIPT)
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)
SHA = "a" * 40


class FakeClient:
    def __init__(self):
        self.heads = []
        self.inline = [{"id": 1, "body": "Please fix the behavior."}]
        self.issues = []
        self.reviews = [{"id": 2, "body": "General review feedback."}]
        self.posts = []
        self.fail_before_write = False
        self.fail_after_write = False

    def get(self, path, page=None):
        if page is None:
            sha = self.heads.pop(0) if self.heads else SHA
            return {"head": {"sha": sha}, "number": 123}
        records = (
            self.reviews if path.endswith("/reviews")
            else self.inline if "/pulls/" in path
            else self.issues
        )
        return deepcopy(records[(page - 1) * 100:page * 100])

    def post(self, path, payload):
        if self.fail_before_write:
            raise review.AuditError("Connection failed before remote acceptance.")
        self.posts.append((path, deepcopy(payload)))
        comment = {
            "id": 9000 + len(self.posts), "body": payload["body"],
            "html_url": f"https://github.example/comment/{9000 + len(self.posts)}",
        }
        if "in_reply_to" in payload:
            comment["in_reply_to_id"] = payload["in_reply_to"]
        (self.inline if "/pulls/" in path else self.issues).append(comment)
        if self.fail_after_write:
            raise review.AuditError("Response lost after remote acceptance.")
        return deepcopy(comment)


def make_plan():
    return {
        "repo": "owner/repo", "pr": 123, "head_sha": SHA,
        "replies": [{
            "kind": "inline", "in_reply_to": 1,
            "body": "[codex] Fixed: the configured backend is selected.",
            "evidence": [f"{SHA} src/client.py:20: backend dispatch"],
        }],
    }


class CollectionTests(unittest.TestCase):
    def test_pagination_keeps_full_bodies_and_discussion_types(self):
        client = FakeClient()
        client.inline = [{"id": i, "body": "x" * 20000} for i in range(1, 102)]
        client.inline[100]["in_reply_to_id"] = 1
        client.issues = [{"id": 200, "body": "Follow-up changes the scope."}]
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "audit"
            snapshot = review.collect(client, "owner/repo", 123, out)
            self.assertEqual(snapshot["counts"], {"inline": 101, "issues": 1, "reviews": 1})
            self.assertEqual(len(snapshot["inline"][-1]["body"]), 20000)
            self.assertEqual(snapshot["threads"][0]["comment_ids"], [1, 101])
            self.assertEqual(snapshot["threads"][0]["resolution_state"], "unknown")
            self.assertTrue((out / "pages" / "inline-0002.json").exists())
            self.assertTrue(json.loads((out / "snapshot.json").read_text())["complete"])
            with self.assertRaises(FileExistsError):
                review.collect(client, "owner/repo", 123, out)

    def test_repeated_page_is_not_marked_complete(self):
        client = FakeClient()
        repeated = [{"id": i, "body": ""} for i in range(100)]
        with patch.object(client, "get", return_value=repeated):
            with self.assertRaisesRegex(review.AuditError, "repeated ID"):
                review.paginate(client, "/comments", "inline")

    def test_head_change_preserves_pages_but_not_complete_snapshot(self):
        client = FakeClient()
        client.heads = [SHA, "b" * 40]
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "audit"
            with self.assertRaisesRegex(review.AuditError, "head moved"):
                review.collect(client, "owner/repo", 123, out)
            self.assertTrue((out / "pages" / "pr-before.json").exists())
            self.assertFalse((out / "snapshot.json").exists())

    def test_truncation_and_invalid_json_fail_closed(self):
        for body in ['{"bodyTruncated": true}', '{"truncated": true}', '[{"id":']:
            with self.subTest(body=body):
                with self.assertRaises(review.AuditError):
                    review.decode(body)

    def test_bga_reads_download_not_inline_preview(self):
        args = argparse.Namespace(
            transport="bga", connection_id="discovered-at-runtime",
            bga_cli=Path("/example/bga-connections"),
        )
        payload = [{"id": 1, "body": "full content " * 10000}]

        def fake_run(command, body=None):
            self.assertEqual(command[1], "download")
            Path(command[command.index("--output") + 1]).write_text(json.dumps(payload))
            return '{"status": 200}'

        with patch.object(review, "run", side_effect=fake_run):
            self.assertEqual(review.Client(args).get("/comments", page=1), payload)


class PostingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.receipts = Path(self.temp.name) / "receipts.jsonl"
        self.client = FakeClient()
        self.plan = make_plan()

    def test_default_preview_has_no_writes_or_receipt_file(self):
        result = review.post_plan(self.client, self.plan, self.receipts)
        self.assertEqual(result[0]["action"], "would-post")
        self.assertFalse(self.client.posts)
        self.assertFalse(self.receipts.exists())

    def test_apply_targets_root_and_second_run_does_not_duplicate(self):
        result = review.post_plan(self.client, self.plan, self.receipts, apply=True)
        self.assertEqual(result[0]["action"], "posted")
        self.assertEqual(self.client.posts[0][0], "/repos/owner/repo/pulls/123/comments")
        self.assertEqual(self.client.posts[0][1]["in_reply_to"], 1)
        states = [json.loads(line)["state"] for line in self.receipts.read_text().splitlines()]
        self.assertEqual(states, ["pending", "confirmed"])
        result = review.post_plan(self.client, self.plan, self.receipts, apply=True)
        self.assertEqual(result[0]["action"], "skip-existing")
        self.assertEqual(len(self.client.posts), 1)

    def test_existing_reply_is_skipped_without_prior_receipts(self):
        self.client.inline.append({
            "id": 9, "in_reply_to_id": 1, "body": self.plan["replies"][0]["body"],
        })
        result = review.post_plan(self.client, self.plan, self.receipts, apply=True)
        self.assertEqual(result[0]["id"], 9)
        self.assertFalse(self.client.posts)

    def test_same_body_in_other_thread_does_not_hide_requested_reply(self):
        self.client.inline += [
            {"id": 2, "body": "Other root"},
            {"id": 9, "in_reply_to_id": 2, "body": self.plan["replies"][0]["body"]},
        ]
        review.post_plan(self.client, self.plan, self.receipts, apply=True)
        self.assertEqual(len(self.client.posts), 1)

    def test_reply_to_reply_is_rejected_before_any_post(self):
        self.client.inline.append({"id": 9, "in_reply_to_id": 1, "body": "Existing reply"})
        invalid = deepcopy(self.plan["replies"][0])
        invalid["in_reply_to"] = 9
        self.plan["replies"].append(invalid)
        with self.assertRaisesRegex(review.AuditError, "root comment"):
            review.post_plan(self.client, self.plan, self.receipts, apply=True)
        self.assertFalse(self.client.posts)

    def test_stale_head_or_missing_evidence_blocks_posting(self):
        self.client.heads = ["b" * 40, "b" * 40]
        with self.assertRaisesRegex(review.AuditError, "differs"):
            review.post_plan(self.client, self.plan, self.receipts, apply=True)
        self.plan["replies"][0]["evidence"] = []
        with self.assertRaisesRegex(review.AuditError, "evidence"):
            review.post_plan(self.client, self.plan, self.receipts, apply=True)
        self.assertFalse(self.client.posts)

    def test_head_is_rechecked_immediately_before_write(self):
        self.client.heads = [SHA, SHA, "b" * 40]
        with self.assertRaisesRegex(review.AuditError, "head moved"):
            review.post_plan(self.client, self.plan, self.receipts, apply=True)
        self.assertFalse(self.client.posts)

    def test_lost_response_recovers_from_remote_without_reposting(self):
        self.client.fail_after_write = True
        with self.assertRaises(review.AuditError):
            review.post_plan(self.client, self.plan, self.receipts, apply=True)
        self.assertEqual(json.loads(self.receipts.read_text())["state"], "pending")
        self.client.fail_after_write = False
        result = review.post_plan(self.client, self.plan, self.receipts, apply=True)
        self.assertEqual(result[0]["action"], "skip-existing")
        self.assertEqual(len(self.client.posts), 1)

    def test_uncertain_missing_post_is_never_automatically_retried(self):
        self.client.fail_before_write = True
        with self.assertRaises(review.AuditError):
            review.post_plan(self.client, self.plan, self.receipts, apply=True)
        self.client.fail_before_write = False
        with self.assertRaisesRegex(review.AuditError, "Prior receipt"):
            review.post_plan(self.client, self.plan, self.receipts, apply=True)
        self.assertFalse(self.client.posts)

    def test_wrong_thread_response_leaves_pending_receipt(self):
        with patch.object(self.client, "post", return_value={
            "id": 9, "body": self.plan["replies"][0]["body"], "in_reply_to_id": 99,
        }):
            with self.assertRaisesRegex(review.AuditError, "Unverified"):
                review.post_plan(self.client, self.plan, self.receipts, apply=True)
        self.assertEqual(json.loads(self.receipts.read_text())["state"], "pending")

    def test_issue_followup_uses_issue_endpoint(self):
        reply = self.plan["replies"][0]
        reply["kind"] = "issue"
        del reply["in_reply_to"]
        review.post_plan(self.client, self.plan, self.receipts, apply=True)
        path, payload = self.client.posts[0]
        self.assertEqual(path, "/repos/owner/repo/issues/123/comments")
        self.assertNotIn("in_reply_to", payload)

    def test_changed_prefix_or_duplicate_plan_is_rejected(self):
        self.plan["replies"][0]["body"] = "Not prefixed"
        with self.assertRaises(review.AuditError):
            review.post_plan(self.client, self.plan, self.receipts, apply=True)
        self.plan = make_plan()
        self.plan["replies"] *= 2
        with self.assertRaisesRegex(review.AuditError, "Duplicate"):
            review.post_plan(self.client, self.plan, self.receipts, apply=True)
        self.assertFalse(self.client.posts)


if __name__ == "__main__":
    unittest.main()
