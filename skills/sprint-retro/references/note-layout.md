# Sprint note layout

Default destination:

```text
~/journal/sprint-retros/sprint-N/
  Sprint N.md
  Slide outline.md
  sources/
    Journal.md
    GitHub.md
    Confluence.md
    SKU100.md
    Slack clarifications.md
```

Create only consulted source notes. Quantitative work can also retain compact
metrics/event/PR-diff ledgers in `sources/`; raw response dumps do not belong in
the presentation notes. Do not copy another sprint's facts, names, dates,
connection IDs or account IDs as new evidence.

## Synthesis

Use frontmatter for the actual window and presentation date. Add separately
named follow-up timestamps when only review activity or merge status advances;
do not silently change the overall coverage end for unrelated sources.

Suggested sections, adapted to the current note rather than regenerated:

- **Retrospective narrative:** the few most important contributions, including
  substantial review and owned implementation.
- **Review workload:** latest running totals with the original snapshot and
  counting qualifications retained or linked.
- **Outcomes and contributions:** workstream, personal contribution, evidence
  and dated status. Name the E2E artifact/result when established.
- **Friction and lessons:** observations paired with actionable lessons,
  including user-authored reflections without rewriting their wording.
- **Proposed next-sprint actions:** only work still outstanding; proposals are
  not assigned team commitments.
- **Coverage and limitations:** source scope, assignment/query gaps, evidence
  attribution, and what was independently checked.

## Source notes

Record the source-specific window, discovery coverage, meaningful contributions,
dated evidence links, personal attribution, and explicit limitations. Keep
source details here instead of inflating the synthesis.

A dated follow-up states what changed, what was verified, and which prior
statements are historical. Preserve original snapshots but keep the top summary
clear about current status. Resolve material conflicts in the synthesis; retain
the original source reports rather than making them falsely agree.

## Slide outline

Default to three sections: outcomes/impact, friction/lessons, and proposed
next-sprint actions. Each has short **on-slide copy**, **speaker notes**, and
compact **evidence pointers**. Combine sections for a requested two-slide version.

Use the latest verified headline review totals with an explicit as-of time.
Keep exact definitions and diff-volume caveats nearby in speaker notes. Carry
implementation, test, merge, deployment and acceptance statuses consistently
through all slides; an old open-PR snapshot must not conceal a later merge.

## Narrow updates

For a formatting correction, alter formatting only: preserve the current words,
remove unintended empty columns/padding, and repair verifiably damaged links.
Escape table wikilink aliases as `[[note\|label]]` so the alias is not treated as
another column. Validate that row structure, link targets and heading anchors
work, and that surrounding text is unchanged.

For a content/status update, patch current sections in place. Check the diff
against a fresh read, not a previous run's synthesized copy. A backup can aid
recovery but is never authority to overwrite live edits.
