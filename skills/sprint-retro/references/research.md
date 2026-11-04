# Source research and delegation

## Assign bounded work

Use the fewest workers that provide useful separation. A fresh cross-source
analysis can split journal/linked notes, GitHub, Confluence, and SKU100. Add a
Slack clarification worker only when a named question remains unresolved.
For a source-specific refresh, reuse that worker; do not repeat all discovery.

Give each worker:

- The sprint, local/UTC window and exact cutoff, identity, output path, and
  relevant existing source notes or ledger.
- Its owned source note, excluded files, required access skills/instructions,
  and the prohibition on remote writes and live system operations.
- A bounded discovery objective and explicit evidence questions. Require
  complete pagination where claiming complete accessible results.
- A concise handoff: contributions, decisive evidence pointers, status at
  cutoff, attribution, gaps, modified paths, and any metrics/ledger locations.

Keep fetched responses in a unique per-run scratch directory, separate from
original evidence. Retain compact, non-secret counting ledgers with the sprint
notes when future updates depend on them. Do not copy credentials, broad raw
message histories, or unrelated personal material into the vault.

Workers must follow the applicable journal/acronym instructions. Do not repeat
an already completed conversation-level acronym gate or block on irrelevant
standalone names.

## Journal and linked notes

Use daily notes as an index. Follow substantive calendar/task transclusions and
important second-level links, resolving exact filenames before guessing.
Skip empty scaffolding and routine lunch blocks; missing weekend notes are a
coverage fact, not evidence of no work.

Daily summaries can seed discovery, but keep plans distinct from completed work
and attribute agent-reported tests. Weekly summaries can include out-of-window
activity and are not independent confirmation.

For mutable daily notes, use timestamped evidence within the cutoff. Pin the
particular immutable session-summary artifact where needed; do not silently
incorporate newer scans during a follow-up. Reuse existing summaries instead of
bulk-loading session batches.

## GitHub

Identify the account, then discover authored, reviewed, commented, mentioned,
and involved PRs alongside journal seeds. PRs merged by the user are activity,
not automatically reviews. Inspect dated review/comment events, descriptions,
metadata, and relevant validation claims; use the separate
[review counting contract](review-metrics.md) for quantitative work.

Keep self-review, colleague review, authored implementation, integration commits,
and merge-only activity distinct. Attribute Codex-assisted posts under the
user's account transparently; do not count native bot accounts as the user.
Do not inspect source checkouts or start containers merely to prepare a retro.

Follow the direct-executable and reusable-approval requirements of
`$bga-readonly`. Use its `--output` option for complete bodies; do not hide
network calls inside a Python/shell batch that bypasses that invocation route.
Fetch bounded groups and surface stalled work promptly. A scratch parsing
script may process already downloaded files; it does not need network access.
On a blocked request, follow the skill's escalation procedure; do not leave
unbounded retries or duplicate fetch jobs running.

## Jira / SKU100

Resolve sprint/board identity from accessible metadata or issue fields.
Audit assigned-ticket coverage independently of activity discovery:

- Search the relevant assignee/project without relying solely on `updated`
  within the reporting window; unchanged assigned tickets otherwise disappear.
- Query exact sprint membership separately. When reporting historical
  assignment/membership, reconstruct it from histories through the cutoff
  rather than treating the present assignment as historical truth.
- Separate current assigned inventory, historical overlap, actual in-window
  work, and old closed backlog. Report set sizes and query coverage; do not
  promote an inventory correction into additional accomplishments.

If a board/sprint endpoint is denied, still try permitted issue/search/history
reads. Explain which filter or metadata remains unverified rather than claiming
all assigned issues are inaccessible.

## Confluence

Use page bodies, account attribution, versions and comments to distinguish
authorship from links or coordination. Separate schema proposals, current
references, SOP indexes, and actual operating instructions; creating an index
does not mean authoring every linked SOP. Do not count duplicate personal-space
copies as independent outcomes.

If version-history listing is unavailable, report that precisely and use allowed
individual-version reads where useful. Publication is not implementation,
deployment, or validation.

## Targeted Slack clarification

Read daily-note Slack summaries first. Search or follow a linked conversation
only to resolve a concrete gap, such as rollout completion, platform processing,
ownership, or acceptance. A linked message may be a reply: find the real parent
thread when a standalone thread read misleadingly returns no replies.

Respect the cutoff and record searched topics/threads. “Not found in these
messages” is not proof that an outcome never happened. If a full thread remains
too broad, narrow by participants, date, and topic instead of sweeping channels.
