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

## Group comments into one review

By default, gather all authorized findings for a PR before posting and submit
them together in **one review**. Put code-specific findings in its `comments`
array and general findings in its summary `body`. Submit once with
`POST /repos/{owner}/{repo}/pulls/{pr}/reviews`, the reviewed `commit_id`, and
`event: "COMMENT"`, unless the user explicitly authorized another verdict.
Each inline body and the summary must still start with `[codex]`.

This groups the feedback into one review submission and reduces notification
noise; do not promise an exact notification count. Do not post each finding
individually and then add a review summary, which duplicates notifications.
Prepare and validate the complete payload, including diff locations and
duplicate checks, before the write. Verify the returned review and all of its
inline comments, and record their IDs/URLs together in the receipt.

For follow-up explanations, prefer one review summary linking the relevant
existing threads when the user has not requested in-thread replies. Replies
to existing threads cannot be bundled in a new review's `comments` array; use
the reply endpoint when in-thread replies are requested and consolidate each
thread's explanation into one reply. Use standalone discussion comments only
when explicitly requested, consolidating related findings into one body.

If the authorized tool cannot submit a grouped review, report that limitation
instead of silently falling back to a series of individual comments. Do not
delete or repost previously published comments merely to regroup them.

Use these endpoints for the selected posting mode:

| Comment type | GitHub REST target and placement |
| --- | --- |
| Standalone PR discussion | `POST /repos/{owner}/{repo}/issues/{pr}/comments` with `body`. |
| Submitted review (default) | `POST /repos/{owner}/{repo}/pulls/{pr}/reviews` with reviewed `commit_id`, authorized `event`, summary `body`, and inline `comments`. Each inline entry contains `body`, `path`, `line`, and `side`; use `start_line`/`start_side` for a range. Anchor to the current diff. Omit `comments` for a summary-only review. |
| Reply to an inline thread | `POST /repos/{owner}/{repo}/pulls/{pr}/comments` with `body` and `in_reply_to` identifying the root comment, not a reply-to-reply. |

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
The helper posts plan entries individually. Do not use it to publish a batch
of findings that belongs in one review.
