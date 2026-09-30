---
name: github-pr-comments
description: Post requested GitHub PR discussion comments, inline review comments, review replies, and review summaries with [codex] attribution. Shared posting workflow for bg-pr-readiness and pr-review-followup; use when posting is requested, not for read-only reviews or audits.
---

# GitHub PR Comments

Post only the comments the user has authorized. A request to review or audit a
PR does not authorize posting. Reuse existing authorization without asking for
another confirmation; tool approvals and provider permissions still apply.
Posting comments does not authorize editing code, resolving threads, changing
the PR description, approving/requesting changes, or merging.

## Attribution

Every posted comment body must begin with the literal `[codex]`, followed by the
comment text. Apply this to standalone PR discussion comments, new inline review
comments, replies, and nonempty review-summary bodies. For a submitted review,
prefix **each** entry in `comments[]` as well as any summary body; prefixing only
the summary is insufficient. Preserve an existing leading `[codex]` rather than
adding it twice. Do not change historical comments merely to add attribution.

## Posting workflow

Use the invoking review skill's verified findings or reply plan as the content;
this skill does not reclassify findings or choose additional comments to post.
For BG repositories, follow the `bga-connections` access guidance and use
`bga-readonly` for supported reads. Use an authorized write-capable connection
for posting; the read-only wrapper cannot post. Authenticated `gh` or a connected
GitHub tool can be used where appropriate. Do not switch transports to evade an
approval or permission denial.

Before posting, recheck the PR head and refresh the relevant discussion to catch
intervening changes or replies. Reassess if the head changed. Read existing
comments to avoid semantic duplicates, not just exact copies; a useful existing
explanation can be left alone.

Choose the target that matches the request:

| Comment type | GitHub REST target and placement |
| --- | --- |
| Standalone PR discussion | `POST /repos/{owner}/{repo}/issues/{pr}/comments` with `body`. |
| New inline review comment | `POST /repos/{owner}/{repo}/pulls/{pr}/comments` with `body`, reviewed `commit_id`, `path`, `line`, and `side`; use `start_line`/`start_side` for a range. Anchor to the current diff. |
| Reply to an inline thread | The same PR comments endpoint with `body` and `in_reply_to` identifying the root comment, not a reply-to-reply. |
| Submitted review | `POST /repos/{owner}/{repo}/pulls/{pr}/reviews` with reviewed `commit_id`, authorized event, optional summary `body`, and any inline `comments`. A request to post comments uses `COMMENT`; do not infer approval or a request-changes verdict. |

Preserve actual newlines through structured arguments or a payload/body file.
For general discussion follow-ups, identify the source comments and consolidate
closely related concerns where that avoids noise.

Verify each creation's ID, body, and intended thread or code location, and keep
a local receipt outside the repository. If a POST times out or returns an
ambiguous response, check the remote discussion before retrying; do not blindly
repost. Return links to the posted comments and report skipped or uncertain
operations accurately.

## Optional helper

[references/helper.md](references/helper.md) documents the shared Python helper
for complete discussion collection, standalone PR comments, and inline replies.
It preserves the existing preview, head checks, duplicate checks, and receipts.
Use the authorized API/tool workflow above for new inline comments or batched
reviews; those are not supported by the helper's reply-plan schema.
