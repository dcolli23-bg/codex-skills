---
name: journal-daily-codex-summary
description: Summarize a workday by reading the user's Slack messages for that date, combining them with the matching `daily/YYYY-MM-DD.md` note and its linked/transcluded calendar notes, then writing or replacing `## Daily Codex Summary` and `## Jira Ticket Candidates` subsections under `# Where I'm Leaving Off`. Use when the user asks to create, update, regenerate, or write a daily Codex summary or daily Jira ticket candidates from Slack plus journal notes.
---

# Journal Daily Codex Summary

## Overview

Create a compact daily summary from two sources: the user's Slack activity for the day and the journal's daily note plus its directly linked/transcluded notes. Write the result into the daily note under `# Where I'm Leaving Off` as `## Daily Codex Summary`, then use the same synthesized context to write `## Jira Ticket Candidates`. The `## Jira Ticket Candidates` section is a Codex-generated suggestion list only; it must not be treated as accepted or planned Jira work without further supporting context or explicit user/team confirmation.

## Workflow

1. Determine the target date.
Use an explicit human-provided date when present. Otherwise, use "today" in the user's Slack profile timezone when Slack is available; if Slack is unavailable, use the environment date. For scheduled or otherwise default daily-summary runs on a Monday, summarize the previous Friday's note rather than Sunday, since weekend daily notes usually do not exist. If a scheduled wrapper passes a computed target date for the previous Sunday, treat it as default date selection and switch to the previous Friday; do not override a date that the human intentionally requested.

2. Resolve the Slack user and search their messages.
Call `slack_read_user_profile` to get the user ID and timezone. Search all accessible Slack surfaces with:

```text
from:<@USER_ID> on:YYYY-MM-DD
```

Use `slack_search_public_and_private` with `content_types="messages"`, `sort="timestamp"`, and `sort_dir="asc"`. Include context on the first search page; page through all results. Read important parent threads only when search context is insufficient to understand the topic, participants, decision, or blocker.

3. Extract Slack themes and people.
Group messages by topic, not by timestamp. Track who the user talked to and where when useful: DMs, group DMs, and named channels. Prioritize decisions, blockers, debugging progress, support work, status updates, and concrete follow-ups. Compress jokes, acknowledgements, and generic coordination unless they clarify a workstream.

4. Read the journal sources.
Open `daily/YYYY-MM-DD.md`. Capture substantive body text, especially `# Where I'm Leaving Off`. Extract `[[wikilinks]]` and `![[transclusions]]` from the daily note and resolve them by exact filename search; prefer matching-date notes in `calendars/`, then task notes. Read only directly linked notes that add concrete work detail.

5. Synthesize Slack plus journal notes.
Merge duplicated topics across Slack and journal notes. The daily note is the user's own framing; preserve it when deciding emphasis. Slack usually adds people, channels, missing details, and conversational context.

6. Identify Jira ticket candidates.
Use the synthesized Slack plus journal context from this run; do not comb back through Slack or reread broad journal sources just for Jira candidates. Look for follow-ups that are concrete enough to become tickets: bugs, investigations, implementation tasks, validation work, deployment/support chores, documentation gaps, or coordination tasks with a clear desired outcome. Skip weak candidates, already-completed work, generic meetings, status updates, personal tasks, and duplicate items.
Treat the candidates as a draft planning aid. Do not phrase them as committed work, accepted backlog items, or tickets that should exist without further supporting context.

7. Write the summary and ticket candidates.
Add or replace `## Daily Codex Summary` and `## Jira Ticket Candidates` under `# Where I'm Leaving Off` in the daily note. If either subsection already exists, replace its contents rather than adding a second copy. Do not remove the user's existing `# Where I'm Leaving Off` bullets.

## Output Format

The `## Daily Codex Summary` section must have at most 3 top-level bullets. Each top-level bullet must be a short title, with exactly one indented sub-bullet containing the details.

Use this shape:

```md
## Daily Codex Summary

- Short title
	- Detail sentence or two with the concrete work, people, decisions, blockers, and next steps.
- Another short title
	- Detail sentence or two.
```

Keep titles concise and scannable. Keep detail sub-bullets information-dense; avoid chronological narration unless the order matters. Mention names and channels when they help the future reader recover context.

The Jira ticket candidates section must have at most 5 top-level bullets. Each candidate should have a ticket-style title and exactly one indented sub-bullet with the suggested ticket type plus enough context to recover why it matters. These are Codex-suggested candidates only, not accepted tickets or committed team work; do not create Jira tickets or treat them as accepted without further supporting context and explicit user/team confirmation.

Use this shape:

```md
## Jira Ticket Candidates

_Codex-suggested candidates only; not accepted tickets without further supporting context._

- Ticket-style title
	- Type: Bug/Task/Investigation/Docs. Context: why this came up, who or what it affects, and the likely acceptance signal.
```

If no strong ticket candidates surfaced, still write the section with one bullet:

```md
## Jira Ticket Candidates

_Codex-suggested candidates only; not accepted tickets without further supporting context._

- No strong Jira ticket candidates surfaced from today's Slack and journal context.
```

## Editing Rules

- Preserve YAML frontmatter, Obsidian wikilinks/transclusions, and existing daily-note text.
- Insert both generated sections inside the `# Where I'm Leaving Off` area.
- Use `apply_patch` for manual edits.
- If the daily note is missing, ask before creating it unless the user explicitly asked to create the note.
- If Slack access fails or search coverage is incomplete, still summarize the journal notes and state the Slack limitation in the chat response.
