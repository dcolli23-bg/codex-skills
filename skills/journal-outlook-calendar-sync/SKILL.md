---
name: journal-outlook-calendar-sync
description: Use when Dylan asks to sync, import, create, or update Obsidian journal calendar notes from Outlook calendar events, especially beginning-of-day workflows that create one journal note per Outlook event and embed those notes in the daily note.
---

# Journal Outlook Calendar Sync

Use this skill to create or update Dylan's Obsidian-style journal notes from Outlook calendar events.

## Required Context

Before syncing, read:

```bash
sed -n '1,220p' ~/journal/AGENTS.md
sed -n '1,220p' ~/journal/calendars/AGENTS.md
```

This skill intentionally skips the `~/journal/UNKNOWN_ACRONYMS.md` startup gate. Do not read or block on unresolved acronyms during calendar sync unless Dylan explicitly asks.

Follow `~/journal/calendars/AGENTS.md` for frontmatter, folder routing, mandatory meeting headings, Outlook ID fields, filename rules, and idempotency behavior.

## Workflow

1. Determine the sync date.
   - Default to today in the user's local timezone from the environment.
   - If the user gives a date, use that exact date.
   - Use a closed-open local-day window: `YYYY-MM-DDT00:00:00-04:00` to next day `YYYY-MM-DDT00:00:00-04:00` during EDT, or the correct local offset for that date.

2. Fetch Outlook events.
   - If Outlook calendar tools are not loaded, discover them with `tool_search` for "Microsoft Outlook Calendar list events".
   - Use the Outlook Calendar `list_events` tool with `start_datetime`, `end_datetime`, `order_by="start/dateTime asc"`, and a generous `top` such as `200`.
   - Use the signed-in user's primary calendar unless Dylan explicitly asks for a shared/delegated calendar.
   - Skip cancelled events. Include accepted, tentative, and organizer events. If a declined event still appears, skip it unless Dylan asked for every visible event.

3. Normalize each event.
   - Convert Outlook start/end to local date and `HH:MM` frontmatter values.
   - Use `display_title` or `subject` as the title.
   - Preserve these Outlook identifiers when available:
     - `outlookEventId`: event `id`; primary idempotency key.
     - `outlookICalUId`: `i_cal_u_id`; fallback key with date and start time.
     - `outlookSeriesMasterId`: `series_master_id`; recurring-series context, not the primary key.
     - `outlookCalendarId`: calendar ID if a non-primary calendar is used.

4. Choose the target note.
   - First search existing calendar notes for `outlookEventId`.
   - If absent, search for `outlookICalUId` plus matching `date` and `startTime`.
   - If absent, search for an existing dated note with the same normalized title, date, start time, and end time.
   - Before choosing a folder, search for prior notes with the same or similar title and reuse the historical folder when obvious.
   - Otherwise apply the folder routing in `~/journal/calendars/AGENTS.md`.

5. Create or update the calendar note.
   - Never overwrite user-written body content.
   - For existing notes, add missing Outlook fields to frontmatter and preserve all other content.
   - For new notes, use the standard frontmatter from `calendars/AGENTS.md`.
   - For new synced `RAD SW Standup` notes, use the standup-specific body scaffold below. Only populate `# Yesterday` with a transclusion of the previous work day's `Daily Codex Summary`; leave the other sections as blank ` - ` placeholders for Dylan.

```markdown
# Things To Update Team On

 - 

# Yesterday

![[YYYY-MM-DD#Daily Codex Summary]]

# Today

 - 

# Notes During Meeting

 - 
```

   - For other new synced meeting notes in `Meetings/`, `Stand Ups/`, or `Interviews/`, include:

```markdown
# Pre-Meeting Prep

 - 

# Notes During Meeting

 - 

# Action Items

 - 
```

   - For `Focus Time/` and `Lunch/`, sparse notes may contain only frontmatter unless useful context exists.
   - Do not include Zoom/Teams dial-in boilerplate, long attendee lists, or generic invite text. Add a short source/context line only when the invite body contains useful non-boilerplate agenda context.

6. Update the daily note.
   - Daily note path: `~/journal/daily/YYYY-MM-DD.md`.
   - If the daily note does not exist, create it from `~/journal/templates/{{date}}.md` and keep the same headings.
   - Under `# Calendar Events`, add one Obsidian transclusion per synced note, for example `![[2026-06-09 RAD Weekly Sync]]`.
   - Separate adjacent calendar transclusions with one blank line in the daily note.
   - Do not duplicate transclusions already present.
   - Keep transclusions in chronological order while preserving non-calendar text the user already wrote.

7. Verify.
   - Read back the modified daily note and any newly created note shapes.
   - Report how many events were fetched, created, updated, skipped, and embedded.
   - Mention any uncertain folder routing or title collisions.

## Editing Rules

Use `apply_patch` for manual file edits. Keep changes scoped to `~/journal/daily/`, `~/journal/calendars/`, and only the requested date unless Dylan asks for a broader repair.

Do not expose private invite content in the final answer. Summarize operationally: file paths, counts, and any decisions that need Dylan's review.
