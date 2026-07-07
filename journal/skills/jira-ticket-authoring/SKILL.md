---
name: jira-ticket-authoring
description: Draft or create general Jira tickets from evidence such as Slack threads, Box documents, Jira links, GitHub context, local files, or pasted notes. Use when Codex needs to turn raw observations into concise Jira-ready issue content, refine an existing ticket draft, or prepare a Jira comment/update without doing code implementation work.
---

# Jira Ticket Authoring

Use this skill when the user wants help writing, refining, or creating Jira ticket content from source material.

Do not use this skill when:
- the task is to implement an existing Jira ticket in code; use `implement-ticket`

Read [references/voice.md](references/voice.md) before drafting so the output matches Dylan Colli's normal Jira tone.

## Inputs

Typical inputs include:
- pasted notes or observations
- Slack threads
- Box documents
- existing Jira tickets
- GitHub PRs or issues
- local logs, screenshots, or files

Treat the source material as evidence. Do not invent missing context.

## Ticket Policy

Default authoring policy unless the user says otherwise:
- project: `SKU100`
- description sections:
  - `### Background`
  - `### Technical Details`
  - `### Definition of Done`

Every section must contain substantive content.

Always include source references in `### Background` when they exist, such as:
- Slack thread links
- Box document links
- related Jira tickets
- GitHub PRs or issues
- local file references when relevant

Format every URL in ticket descriptions, Jira comments, and user-facing ticket drafts as a Markdown hyperlink. Do not leave bare URLs in drafted or written ticket content. Prefer descriptive labels that name the destination, for example:
- `Source thread: [Slack thread about <topic>](<url>)`
- `Pick Inspector: [<site/system> pick inspector example](<url>)`
- `Related ticket: [RSPS-1234 - <summary>](<url>)`
- `PR: [berkshiregrey/<repo>#1234](<url>)`

## Workflow

1. Identify the user's actual goal:
- draft a new ticket
- refine an existing draft
- prepare a Jira comment/update
- create the ticket in Jira

2. Extract the operational core:
- what happened
- where it happened
- why it matters
- what exact evidence supports it
- what is still unknown

3. Separate fact from inference:
- facts come from the provided evidence
- inference is allowed only when it is weakly interpretive and clearly signaled
- if an important conclusion is uncertain, state the uncertainty instead of smoothing over it

4. Build the Jira structure:
- `### Background`: concise problem statement, system/site context, impact, and source references
- `### Technical Details`: exact technical evidence, system names, logs, screenshots, links, constraints, and related tickets
- `### Definition of Done`: concrete investigation, fix, validation, or handoff outcomes

5. Keep the draft concise by default.
- Prefer a short operational paragraph over a long narrative.
- Expand only if the user asks for more detail or the evidence genuinely requires it.

## Voice Rules

Match Dylan Colli's ticket-writing style:
- direct
- concrete
- operational
- lightly conversational, not formal
- focused on observed behavior and next action
- skeptical of vague language

Prefer titles that name the concrete problem or task directly.

Prefer body text that:
- starts with the real-world problem or observed behavior
- names the site, system, or component early when known
- explains why the issue matters in practical terms
- preserves exact links, ticket keys, parameter names, and error strings when they matter
- renders links as Markdown hyperlinks instead of bare URLs
- ends with a pragmatic definition of done, not generic project language

Avoid:
- padded executive-summary prose
- generic process filler
- abstract wording when a concrete system name is available
- inventing certainty from weak evidence

## Required Evidence Handling

If critical information is missing:
- do not invent it
- state the gap explicitly
- ask for the missing input or mark the draft as incomplete

Examples of often-missing but important details:
- affected site or environment
- exact failing behavior
- expected behavior
- reproducibility
- direct supporting links
- impacted subsystem or owner

## Jira Comments And Updates

If the user wants an update to an existing Jira ticket:
- do not rewrite the whole ticket unless asked
- draft a standalone Jira comment
- include the new evidence and its source
- preserve the existing ticket narrative

Prefer a short heading such as:
- `Additional Context`
- `Additional Evidence`
- `Follow-up From <source>`

## Jira Write Safety

Do not create, edit, transition, or comment on Jira issues unless the user explicitly authorizes that specific write action.

Drafting ticket content in chat is allowed by default. Actual Jira writes require explicit permission.

## Output Rules

When presenting a new ticket draft, provide:
- a proposed title
- the issue type if relevant
- the Jira-ready body

When presenting a Jira comment draft, provide only the comment body unless the user asks for alternatives.

When mentioning Jira tickets in the response:
- include the ticket key, summary, and direct browser URL on the same line
- use clickable Markdown links when possible

If the user asks for multiple ticket options, provide the strongest option first and include a short reason for the tradeoff.
