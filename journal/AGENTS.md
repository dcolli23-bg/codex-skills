# AGENTS.md

## Purpose

This repository is an Obsidian-style work journal. Treat it as operational memory for Dylan's day-to-day engineering work, not as a conventional software repo. Most requests will involve reading, summarizing, organizing, or creating Markdown notes.

## Vault Structure

- `daily/YYYY-MM-DD.md`: daily index notes. These usually contain calendar links/transclusions and a `# Where I'm Leaving Off` section.
- `calendars/`: detailed time-block notes, usually the source of real work detail.
  - `Focus Time/`: implementation, debugging, testing, planning.
  - `Meetings/`, `Stand Ups/`, `Interviews/`, `Lunch/`: meeting and calendar-derived notes.
- `weekly/weekly-summary-YYYY-MM-DD.md`: weekly summaries. The date is the Monday of the summarized week.
- `tasks/`: project/task notes, especially AutoStore, Skild/RFM, Generalist, camera investigations, MF IS pipeline, etc.
- `acronyms/`: lightweight glossary notes for Dylan's recurring acronyms, shorthand, people abbreviations, and domain terms.
- `UNKNOWN_ACRONYMS.md`: unresolved acronym, shorthand, person, product, site, or domain-term questions that need Dylan's clarification.
- `kanban-boards/`: Obsidian Kanban plugin boards. Preserve plugin metadata and formatting.
- `career/`: performance review, goals, and career-growth notes.
- `interviews/` and `resumes/`: candidate/interview material. Handle with extra discretion.
- `templates/`: note templates. Prefer these when creating new notes.
- `.codex/skills/journal-last-week-summary/`: local workflow for generating weekly summaries.

## Calendar Notes

Calendar events are represented as dated block notes under `calendars/`, then embedded from the matching daily note under `# Calendar Events`. When creating or updating calendar-derived notes, read `calendars/AGENTS.md` for the detailed layout, Outlook sync metadata, folder routing, and idempotency rules.

Generated Outlook event notes should preserve existing user-written content. Treat Outlook metadata as synchronization state, not as the main note content.

## Reading Strategy

On the initial assistant turn of a new conversation, before any other action in this vault, read `UNKNOWN_ACRONYMS.md`. Treat it as a one-time startup gate for that conversation, not a per-turn requirement. If `## Unresolved` contains unchecked entries other than standalone first-name references and the session is interactive, ask Dylan to clarify them before continuing with the original request, unless Dylan explicitly says to skip acronym clarification for that turn. Do not repeat this check or request clarification on later turns in the same conversation. Standalone first names (for example, `John` or `Will`) may remain unresolved for context, but must not block work or trigger a clarification request by themselves. When Dylan clarifies a term, add or update the matching concise note in `acronyms/` and remove or mark the entry resolved in `UNKNOWN_ACRONYMS.md`.

Start with `rg --files` and targeted `sed -n` reads. Do not bulk-load the vault unless necessary.

Daily notes often contain `[[wikilinks]]` or `![[transclusions]]`. The linked/transcluded notes usually contain the important details. Resolve links by exact filename search first; if duplicates exist, prefer notes with the same date and a calendar/task path that matches the context.

Skip or compress low-signal notes such as empty standups, lunch blocks, calendar metadata, and notes that only say "morning work" without details.

If you encounter an unfamiliar acronym, shorthand, person abbreviation, product name, customer/site label, or domain term, search `acronyms/` first. If the term is missing but the current notes or user clarify it, add or update a concise note in `acronyms/` so future agents inherit the context. If the meaning is still not confirmed, do not guess or silently create an uncertain glossary entry; add or update an unresolved entry in `UNKNOWN_ACRONYMS.md` with the term, source/context, and the question Dylan should answer. Do not add unresolved entries for standalone first names unless Dylan specifically asks to identify that person or the identity is necessary to complete the task. Do not add unresolved acronym entries for interview candidate names; candidate context belongs in `interviews/` notes and should be handled with extra discretion.

## Common Work Themes

Expect recurring context around robotics software, P2 robots, AutoStore, RFM, Skild, Generalist/SUMI, RPC, Element Logic, Billerica/Bedford commissioning, Kubernetes, networking, ROS/ROS2, cameras/ZED/Jetson, perception, interviews, and AI-agent workflows.

## Jira Ticket Authoring
- Default project policy: when creating Jira tickets, use the `SKU100` project unless the user explicitly requests a different project.
- Prefer concise ticket drafts by default: keep each required section short, high-signal, and focused on the immediate bug or work item unless the user asks for more detail.
- Include source references in `### Background` for every created Jira ticket whenever they exist, such as Slack threads, Box documents, related Jira issues, or GitHub links.
- When creating Jira tickets, always populate all three required sections in the description using Markdown heading level 3:
  - `### Background`
  - `### Technical Details`
  - `### Definition of Done`
- Each required section must contain substantive content; do not leave any section empty or placeholder-only.

## Summaries

For weekly summaries, use the existing local skill if available:
`.codex/skills/journal-last-week-summary/SKILL.md`.

When summarizing, prefer concrete outcomes over chronology:
- implementation progress
- debugging/root cause findings
- testing and validation
- design decisions
- operational support
- hiring/interview work when it consumed meaningful time

Do not summarize sensitive details more specifically than needed.

## Editing Rules

Preserve:
- YAML frontmatter
- Obsidian wikilinks/transclusions
- existing headings and note style
- Kanban plugin metadata blocks

Use existing templates for new notes where applicable. Keep edits narrow and avoid reorganizing the vault unless explicitly asked.

When updating `acronyms/`, keep each note short: meaning, how Dylan usually uses it, and closely related terms. Prefer one note per term, with Obsidian aliases for alternate spellings. Do not silently leave new uncertain glossary entries behind; either ask for clarification before writing them, or write them as explicitly uncertain and ask for correction in the final response.

When updating `UNKNOWN_ACRONYMS.md`, keep it short and actionable. Prefer unchecked bullets under `## Unresolved`; move clarified terms to `## Resolved` only when retaining that history is useful.

## Privacy And Safety

This vault contains work-internal details, career notes, interview notes, resumes, and possibly credential-like material. Do not open or expose secret-looking files unless explicitly asked. In particular, avoid `software/github-recovery-codes.txt`.

When answering broad questions about Dylan or the journal, summarize patterns and themes rather than quoting private notes at length.
