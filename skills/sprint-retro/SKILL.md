---
name: sprint-retro
description: Research Dylan's sprint retrospectives, maintain source-linked Obsidian notes and review-workload totals, and draft a short slide outline. Use for a new sprint retro or a targeted update to an existing one.
---

# Sprint Retro

Build an evidence-backed retrospective in `~/journal/sprint-retros/sprint-N/`.
Default to source notes, a synthesis, and a **three-slide Markdown outline with
speaker notes**; honor a requested two-slide version. Create an actual deck only
when requested, using `$sprint-retro-powerpoint` for the BG template and Box
render-and-verify workflow.

## Establish the reporting contract

Read the applicable home/vault instructions and the current sprint notes before
writing. For a new sprint, establish:

- Sprint identifier, presentation date, and the user's actual-work window.
  Capture an exact cutoff with local timezone and UTC equivalents. Resolve
  relative dates from the current local date; account for DST.
- Jira's formal sprint dates/board identity, recorded separately. They do not
  override the user's requested work window.
- Included sources, output paths, and known access gaps. Default to daily and
  linked journal notes, GitHub, Confluence, and SKU100; use existing daily Slack
  summaries before narrowly searching Slack for unresolved context.

If the window is missing, investigate planning notes and propose concrete dates
instead of silently adopting Jira's dates. Give a bounded plan and use `$grill`
for material unresolved decisions. Reuse approved preferences; do not restart
Grill for routine refreshes or formatting corrections.

## Coordinate research

For a new cross-source analysis, coordinate source-specific workers using
[the research workflow](references/research.md). Dylan's saved preference is
**Terra-medium research agents** when available; resolve the available model
identifier rather than hardcoding a version. If unavailable, disclose that and
use the inherited model. If delegation itself is unavailable, disclose the
limitation before switching to direct research.

Workers own disjoint source notes and return concise results with evidence
pointers, qualifications, and gaps. The coordinator owns the synthesis and slide
outline; do not have multiple workers edit them. Read detailed evidence only for
conflicts, important claims, and validation. Handle small edits directly; reuse
relevant workers for targeted source updates rather than launching a full sweep.

Use `$bga-readonly` and its required organization access guidance for BG GitHub,
Jira, and Confluence. Never use legacy Rovo. Discover permissions and use approved
read endpoints; report specific limitations rather than assuming missing access.
No retrospective request authorizes remote posting, code changes, robot/container
operations, rerunning operational tests, or vault commits/pushes.

## Build the notes and presentation

Use [the note layout](references/note-layout.md) without creating empty source
notes for sources that were not consulted. Write progressively as workers finish.

- Represent review, investigation, implementation, testing, documentation,
  deployment, and coordination—not just authored or merged PRs. Ask which work
  deserves emphasis only if the evidence and user priorities leave that unclear.
- Quantify review activity and diff volume using
  [the counting rules](references/review-metrics.md). Keep colleague reviews
  separate from self-authored PR activity. Counts are not measured hours.
- Separate implemented, reviewed/approved, merged, deployed, E2E-tested, and
  formally accepted states. An open PR does not mean no implementation or
  deployment occurred; merge does not establish runtime acceptance.
- Attribute first-person confirmations to Dylan and source reports to their
  actual authors. Incorporate explicit outcome corrections without presenting
  earlier absence of evidence as a refutation. Keep earlier observations as
  historical evidence; do not invent exact times, cell counts, or sign-off.
- Distinguish assigned tickets, work active in the window, team outcomes, and
  Dylan's contributions. Ticket closure alone is not a new accomplishment.

The default slide sequence is **outcomes/impact → friction/lessons → proposed
next-sprint actions**. Keep on-slide copy short; put definitions, caveats, and
source pointers in speaker notes. Label proposed actions as proposals, not team
commitments. Balance substantial owned implementation with review workload.

## Refresh without losing work

For an existing retro, inspect the latest file immediately before editing.
Patch only the requested sections against that content. Do not replace the
whole note from a cached copy, regenerate user-authored tables, or restore a
backup over intervening edits. If content changes during the edit, reread and
reconcile; preserve unrelated text.

Use targeted, dated follow-ups for merges, outcomes, and added review activity.
Preserve the original cutoff and baseline; state which source coverage advanced.
For review updates, add new event IDs and new unique PR snapshots under the
counting rules rather than counting a full diff again on every re-review.
Reconcile affected headlines, speaker notes, source banners, and next actions so
historical pending-work statements are not presented as current.

If the user cancels, stop workers and fetches started for this task, leave the
last verified totals intact, and remove only unverified edits made by this run.
Do not continue researching or overwrite other edits during cleanup.

## Validate and hand off

Check source attribution, exact windows, totals, PR/status scope, local links and
heading anchors. For tables, check column counts and escape alias pipes inside
table wikilinks (`[[note\|label]]`). On narrow edits, verify surrounding content
and user wording are unchanged.

For a substantial initial analysis or quantitative refresh, use an independent
worker to sample evidence or recompute the cached metrics, without expanding the
research scope. Report specific limitations if that check is unavailable. A
consistency review is not independent operational testing.

Return the note/outline locations, key results or changes, and any material gaps.
Do not keep polishing after the requested work and checks are complete.
