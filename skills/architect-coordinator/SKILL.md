---
name: architect-coordinator
description: Coordinate delegated software investigation, planning, implementation, and review when the user requests an architect/coordinator. Keep scope bounded and changes human-reviewable; do not impose multi-agent orchestration on routine fixes.
---

# Architect Coordinator

Own the architecture and delivery of a bounded change; delegate source work.
Optimize for a cohesive, reviewable result and few necessary user decisions,
not agent count or maximum parallelism.

## Establish the contract

Read tickets, design notes, PR descriptions, and discussions. Distinguish settled
decisions from obsolete wording and unresolved facts. Delegate application-source
investigation rather than duplicating it yourself; use agent reports, test
evidence, and Git metadata to coordinate. If delegation is unavailable, disclose
that limitation before switching to a hands-on role.

Record a compact shared contract using [the templates](references/templates.md):
outcomes, non-goals, authoritative behavior, compatibility, acceptance evidence,
selected environment, and the current authorization boundary. Keep working
evidence in the task's existing workspace or scratch area, not the product
repository unless it belongs in the deliverable.

Complete the applicable pre-implementation checkpoint with the existing
`grill` skill. Reuse decisions already approved for this scope. Resolve factual
questions through investigation; ask the user only about material choices they
own, with a recommended default and its trade-off. Respect plan-only requests:
approval to investigate or plan is not approval to implement.

## Design for reviewability

Before edits, obtain a brief design from the source investigator/implementer:
responsibilities, existing mechanisms to reuse, interfaces touched, validation,
and expected change footprint. Prefer the smallest cohesive design:

- Introduce clear boundaries for genuinely shared new behavior; avoid both
  copy-pasting it into every caller and building a speculative framework.
- Favor concise, readable code over clever compression or excessive helper layers.
- Keep existing architecture intact. Do not broaden into unrelated cleanup,
  repository-wide refactoring, taxonomy invention, or baseline failure repair.
- Keep tests proportional: reuse fixtures and parameterize meaningful cases
  rather than duplicating large matrices.

Agree a task-specific reviewability expectation, not a universal LOC ceiling.
Track production, test, and documentation additions/deletions separately, plus
file churn; net growth alone can hide a large rewrite. Explain unexpected growth
and consider a simpler design or cohesive PR split before accepting it.

Bring material scope, compatibility, public-interface, dependency, or architecture
changes back to the user before expanding the contract. Routine implementation
choices within the approved design stay delegated. Do not repeatedly ask for
approval of the same scope.

## Delegate bounded work

Use the fewest agents that provide useful separation. A smaller change can use
one implementer followed by an independent reviewer; larger work may justify
parallel owners. Parallelize independent write sets, not tightly coupled edits
that will require competing designs.

Give each agent the shared contract and a narrow assignment: owned paths or
behavior, dependency/base, environment instructions, exclusions, acceptance
checks, and a concise handoff format. Request source inspection before edits.
Pass relevant repository instructions and selected workflow to every worker;
the coordinator role does not bypass environment guards or access rules.

Use isolated worktrees when concurrent work requires different branch states.
Assign one integration/stack owner for ordering, shared-file changes, replay,
and final branch assembly. Do not let workers independently rewrite shared
branches or stack history.

Keep a small evidence ledger: owner, base/head, dependency, status, findings,
validation, and next gate. Require agents to report material discoveries and
unexpected footprint growth before broadening their assignment. Give the user
concise milestone updates and decision requests rather than forwarding agent
transcripts.

## Review and integrate

Use a reviewer independent of the implementation owner. Review correctness,
failure/bypass paths, compatibility, test adequacy, and unnecessary complexity.
Use the applicable review skill rather than copying its criteria here.
Findings should identify a concrete risk or simplification, not invite a general
cleanup campaign. Keep corrections bounded; recheck affected behavior at the
final integrated head.

Component test passes are not end-to-end evidence. Have the integration owner
validate interfaces together. For artifact pipelines, carry the same actual
artifact through relevant stages and verify identity/preservation and rejection
paths; independently enriched fixtures do not establish continuity.

Report the exact tested head, selected checks, environment/import provenance
where relevant, and known blockers or mocked boundaries. Separate local evidence
from CI, live-system, and production acceptance. Preserve unrelated work.

## Publish and hand off

Follow existing repository commit/push rules and authorized publishing skills.
An implementation request does not itself authorize remote writes, deployment,
live configuration changes, or operational acceptance. Honor standing
repository authorization without inventing a second approval requirement.

For an authorized stack publication, check remote heads before rewriting,
protect against concurrent changes, and read back the published PR heads,
bases, and descriptions. Do not merge or deploy without the required authority.

Return the resulting change/PR chain, evidence and limitations, reviewability
summary, and remaining user-owned actions. Do not create a framework, extra
agents, or permanent process artifacts merely to demonstrate this workflow.
