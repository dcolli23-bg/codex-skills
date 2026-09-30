# Shared discussion helper

The implementation and usage reference now belong to
[github-pr-comments](../../github-pr-comments/SKILL.md).
Read its [helper reference](../../github-pr-comments/references/helper.md) for
collection, reply-plan format, preview/apply behavior, and receipts.

The existing collection command remains supported:

```bash
python3 ~/.codex/skills/pr-review-followup/scripts/pr_review.py collect \
  --transport bga --connection-id DISCOVERED_ID \
  --repo OWNER/REPO --pr 123 --out /tmp/pr-123-audit
```

`scripts/pr_review.py` delegates to the shared implementation for both `collect`
and the existing `post` command. Use the shared skill for any posting request;
the old command path does not bypass its attribution or authorization rules.
