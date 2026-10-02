---
name: github-pr-comments
description: Post requested GitHub PR discussion comments, inline review comments, review replies, and review summaries with [codex] attribution. Shared posting workflow for bg-pr-readiness, bg-pr-review, and pr-review-followup; use when posting is requested, not for read-only reviews or audits.
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
comments, replies, and nonempty review-summary bodies. For a pending or submitted
review, prefix **each** entry in `comments[]` as well as any summary body;
prefixing only the summary is insufficient. Preserve an existing leading `[codex]` rather than
adding it twice. Do not change historical comments merely to add attribution.
For new findings from `bg-pr-readiness` or `bg-pr-review`, put a concise rule
or finding title on that first line: `[codex] <title>`. Put the explanation in
the following paragraph. Do not impose that title format on replies to existing
threads or unrelated standalone comments.

## Markdown formatting

Wrap inline code in Markdown backticks so it renders correctly in GitHub.
Apply this to identifiers, function calls, parameter names, paths, commands,
and short code expressions in comments, replies, and review summaries, for
example `verify_mcap()`, `chunk_size_bytes`, and `event: "COMMENT"`. Preserve
the literal backticks in the body sent to GitHub; do not escape them as prose.

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

## Group comments into one pending review

By default, gather all authorized findings for a PR and save them together in
**one pending review**. Put code-specific findings in its `comments` array and
general findings in its summary `body`. Create it with
`POST /repos/{owner}/{repo}/pulls/{pr}/reviews` and the reviewed `commit_id`;
**omit `event`** so GitHub leaves the review pending. Do not send
`event: "COMMENT"`, which submits the review. Each inline body and any summary
must still start with `[codex]`.

Dylan will inspect and edit the pending review in GitHub and submit it manually.
Authorization to post findings is authorization to save this pending review,
not to submit it. Submit only when Dylan explicitly requests submission; use
`COMMENT` unless he explicitly authorizes another verdict. Do not publish
individual findings before creating the pending review.

Check for an existing pending review by the authenticated user before creating
one. Preserve its draft comments and summary. Reuse it only through a supported
operation that keeps it pending; if that operation is unavailable, report the
limitation rather than submitting, deleting, or replacing the existing draft.
Prepare and validate the complete payload, including diff locations and
duplicate checks, before the write. Verify that the saved review is `PENDING`
and contains all intended inline comments and summary text. Record their
IDs/URLs together in the receipt and identify the result as awaiting Dylan's
manual submission.

For follow-up explanations, prefer one pending review summary linking the
relevant existing threads when the user has not requested in-thread replies.
Replies to existing threads cannot be bundled in a new review's `comments` array; use
the reply endpoint when in-thread replies are requested and consolidate each
thread's explanation into one reply. Use standalone discussion comments only
when explicitly requested, consolidating related findings into one body.

If the authorized tool cannot save a pending review, report that limitation
instead of submitting a review or publishing individual comments. Do not
delete or repost previously published comments merely to regroup them.

Use these endpoints for the selected posting mode:

| Comment type | GitHub REST target and placement |
| --- | --- |
| Standalone PR discussion | `POST /repos/{owner}/{repo}/issues/{pr}/comments` with `body`. |
| Pending review (default) | `POST /repos/{owner}/{repo}/pulls/{pr}/reviews` with reviewed `commit_id`, summary `body`, and inline `comments`; omit `event`. Each inline entry contains `body`, `path`, `line`, and `side`; use `start_line`/`start_side` for a range. Anchor to the current diff. Omit `comments` for a summary-only review. |
| Submit an existing pending review (explicit request only) | `POST /repos/{owner}/{repo}/pulls/{pr}/reviews/{review_id}/events` with the explicitly authorized `event` and any authorized summary `body`. |
| Reply to an inline thread | `POST /repos/{owner}/{repo}/pulls/{pr}/comments` with `body` and `in_reply_to` identifying the root comment, not a reply-to-reply. |

Preserve actual newlines through structured arguments or a payload/body file.
For general discussion follow-ups, identify the source comments and consolidate
closely related concerns where that avoids noise.

Verify each creation's ID, body, and intended thread or code location, and keep
a local receipt outside the repository. If a POST times out or returns an
ambiguous response, check remote reviews (including the authenticated user's
pending review) and comments before retrying; do not blindly repost. Return a
link to the saved review, or the PR if no review URL is available, and report
its pending/submitted state and any skipped or uncertain operations accurately.

## Optional helper

[references/helper.md](references/helper.md) documents the shared Python helper
for complete discussion collection, standalone PR comments, and inline replies.
It preserves the existing preview, head checks, duplicate checks, and receipts.
Use the authorized API/tool workflow above for new inline comments or batched
reviews; those are not supported by the helper's reply-plan schema.
The helper posts plan entries individually. Do not use it to publish a batch
of findings that belongs in one review.
