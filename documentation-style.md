# Documentation Style

Default to concise, reader-facing documentation. Optimize for finding and using
the answer, not for recording everything investigated.

## Core conventions

- Lead with the purpose, contract, or required action.
- Include what the reader needs to understand the interface or complete the task.
  Prefer precise headings, tables, and lists when they improve scanning.
- Preserve useful illustrative examples. Label synthetic or abbreviated examples
  and keep them consistent with the documented contract. An example is not
  evidence of deployment or completed validation.
- State each important caveat once, near the relevant content. Replace vague
  qualifiers such as "normally" with a clear expected contract and, if necessary,
  a separate historical-data caveat.
- Link to supporting detail rather than duplicating it. Keep source provenance
  compact; omit investigation narratives and test transcripts unless requested.
- Preserve necessary constraints, units, error behavior, failure handling, and
  safety information. Concise does not mean incomplete; do not impose a hard
  word limit.
- Match the document's purpose. Implementation details belong in implementation
  or design documentation, not every interface reference.

## Match the document type

| Document | Include |
| --- | --- |
| API/schema reference | Files, records, fields, expected types, presence, units/shapes, relationships, and what each value captures; useful examples. |
| Guide/runbook | Prerequisites, ordered actions, necessary commands, expected results, and relevant failure/recovery and safety information. |
| Design/implementation doc | The problem, decisions, material rationale/trade-offs, and implementation details needed by its audience. |
| Proposed specification | The proposed contract, clearly distinguished from current or deployed behavior; retain enough context for the requested scope. |
| Additive changelog | Only additions and their associated constraints/examples. Mention existing fields only where needed to explain the additions. |

For API/schema tables, use **Expected type** for intended metadata types; distinguish
them from observed serialized types if they differ. State optionality, units, and
array shapes where relevant. Do not invent a stronger type guarantee than the
source establishes.

Keep current contracts, proposals, and changelogs distinct. Do not automatically
produce all three documents when the request needs only one.

## Editing existing documentation

Apply the style to new documentation and requested rewrites. For a narrow edit,
make the requested change without restructuring or shortening unrelated content.
Preserve required templates and established task- or repository-specific
conventions; use this guide as the default where those leave room.

This guide does not replace the separate conventions for chat, Jira tickets, PR
reviews, or personal journal notes unless Dylan explicitly requests that scope.

## Positive examples

These are models of structure and level of detail, not universal schema rules.
The guide remains usable without fetching them for every documentation task.

| Format | Current reference | Proposed reference | Additive changelog |
| --- | --- | --- | --- |
| MCAP | [Current schema](https://berkshiregrey.atlassian.net/wiki/spaces/RAD/pages/3731554412) | [Proposed spec](https://berkshiregrey.atlassian.net/wiki/spaces/RAD/pages/3731882032) | [Proposed additions](https://berkshiregrey.atlassian.net/wiki/spaces/RAD/pages/3731882059) |
| H5 | [Current schema](https://berkshiregrey.atlassian.net/wiki/spaces/RAD/pages/3731095705) | [Proposed spec](https://berkshiregrey.atlassian.net/wiki/spaces/RAD/pages/3731456176) | [Proposed additions](https://berkshiregrey.atlassian.net/wiki/spaces/RAD/pages/3731128474) |

Before handing off, remove repetition, check example consistency, and confirm
that shortening has not removed information needed to use the document safely.
