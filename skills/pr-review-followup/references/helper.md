# Optional retrieval and posting helper

`scripts/pr_review.py` uses only Python's standard library. It does not analyze
code, classify feedback, or choose which comments to post; those are agent
judgments governed by `SKILL.md`.

## Access

Use working connector tools directly if they expose complete discussions.
Otherwise select one helper transport:

- `--transport gh`: uses an already authenticated `gh api`; does not authenticate
  or change accounts.
- `--transport bga --connection-id ID`: discover the ID with the
  `bga-connections` skill's `list` command. The default CLI path is
  `~/.codex/skills/bga-connections/bga-connections`; override with `--bga-cli`.
  Provider credentials stay with the existing gateway. GETs use `download`
  rather than the gateway's bounded inline preview.

Do not change transport to evade an approval or permission denial.

## Collect

```bash
python3 ~/.codex/skills/pr-review-followup/scripts/pr_review.py collect \
  --transport bga --connection-id DISCOVERED_ID \
  --repo OWNER/REPO --pr 123 --out /tmp/pr-123-audit
```

Use a new output directory each time. `pages/` contains complete source payloads;
`snapshot.json` is written only after all collections and head checks succeed.
It includes PR metadata, comments, reviews, grouped threads, and counts. Partial
directories are retained for diagnosis but must not be described as complete.

The helper requests pages of 100 until a shorter page appears. Repeated IDs,
invalid/truncated JSON, provider errors, or a moving PR head stop the collection.
It does not infer GitHub thread resolution from REST data.

## Stage replies

After comparing the pushed code and reviewing prior explanations, write a plan
outside the repository. A plan is separate from the comprehensive audit: it
contains only replies the user authorized and the agent verified.

```json
{
  "repo": "OWNER/REPO",
  "pr": 123,
  "head_sha": "COPY_THE_AUDITED_PR_HEAD_SHA",
  "replies": [
    {
      "kind": "inline",
      "in_reply_to": 123456789,
      "body": "[codex] Addressed in COMMIT: brief, specific explanation.",
      "evidence": ["COMMIT path/to/file.py:42: what was verified"]
    },
    {
      "kind": "issue",
      "body": "[codex] Follow-up to issue comment 987654321: explanation.",
      "evidence": ["COMMIT path/to/other.py:18: what was verified"]
    }
  ]
}
```

`in_reply_to` must identify a root inline comment from this PR.
The helper checks that bodies start with `[codex]` (or `--prefix`), evidence is
nonempty, target IDs are valid, and the current PR head matches the audited SHA.
It cannot verify the truth of evidence or detect paraphrased duplicate replies.

## Preview, then post only if authorized

```bash
python3 ~/.codex/skills/pr-review-followup/scripts/pr_review.py post \
  --transport bga --connection-id DISCOVERED_ID \
  --plan /tmp/pr-123-replies.json --receipts /tmp/pr-123-receipts.jsonl
```

Without `--apply`, this performs fresh reads and previews decisions; it sends no
POSTs and creates no receipts. Existing identical bodies on the same target are
skipped. Review the full plan as well as preview output before posting.

Run the same command with `--apply` only after the user's posting request.
The helper serializes access to the specified receipt file and writes/fsyncs a
pending receipt before each POST. It verifies creation responses and records
the returned IDs/URLs. Reuse that receipt file on later attempts.

A pending operation with no matching remote comment **blocks retry**. If the
remote body appears on a later run, the helper records recovery without posting
again. Otherwise inspect the thread/provider before deciding how to proceed;
there is deliberately no automatic "force retry." A confirmed receipt whose
comment is no longer present also requires inspection, not automatic reposting.

This is best-effort duplicate prevention, not a distributed exactly-once
guarantee. Do not run concurrent posting workflows with different receipt files.
The head is checked before each write, but GitHub does not provide an atomic
"post only if head unchanged" operation.

Tests use fake transports and temporary directories; they require neither
GitHub access nor credentials. Run them only in an authorized local workflow:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s skills/pr-review-followup/tests -v
```
