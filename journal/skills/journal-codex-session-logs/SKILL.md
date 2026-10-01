---
name: journal-codex-session-logs
description: Collect local Codex session activity into the Obsidian journal and refresh concise, evidence-backed Codex Session Logs in daily notes. Use for Codex activity journaling, replaying collected activity, or maintaining the desktop collector and laptop summary jobs. Summarization and daily-note updates belong only on the laptop.
---

# Journal Codex Session Logs

This workflow uses stdlib Python 3.10+ and the installed Codex CLI. No venv or
Python SDK is required. Read [the activity/storage contract](references/activity-format.md)
when diagnosing records, filtering, or checkpoints. For installation on both
machines, sync verification, and troubleshooting, read
[the installation guide](references/installation.md).

## Run the pipeline

Use the local `~/.config/codex-activity/config.json`. The desktop
(`dcolli23@dylan-lambda`, device `desktop`) only collects. The laptop
(`dylan.colli@ltmj0ffwl3`, device `laptop`) collects, summarizes, and edits notes.
Machine paths and authentication stay outside Git.

- Collect without any model calls:
  `python3 scripts/collect.py`
- On the laptop, refresh available daily-note sections:
  `python3 scripts/summarize.py`
- Reconcile a particular day from filtered evidence:
  `python3 scripts/summarize.py --date YYYY-MM-DD --reconcile`
- Refresh session logs, then run the normal Slack/journal daily-summary skill:
  `python3 scripts/daily.py` (previous workday), or pass `--date YYYY-MM-DD`.

Paths above are relative to this skill. Resolve them before execution. All scripts
accept `--config PATH`. Do not override `writer` on the desktop to edit real notes.
Do not run these commands recursively from the model summarization prompt or when
`CODEX_ACTIVITY_PREPARED=1`; the outer daily job already holds the writer lock.

## Summary behavior

The scripts invoke `gpt-6-luna` with `high` reasoning for new evidence chunks and
full-day synthesis. Keep grouping conservative: a shared repository or similar
session title is insufficient to merge separate objectives. Include non-code
work and decisions. Distinguish discussion, plans, attempts, and observed results;
never report tests, commits, pushes, or deployments as completed without support.

Accomplishments and significant decisions accumulate; current blockers and next
steps change as later evidence supersedes them. Chunk summaries and raw filtered
records remain available. The daily note is a derived view, never the input to an
iterative compression loop. Closed days are reconciled from filtered records;
late synced activity triggers reconciliation again and queues the normal daily
summary for the next daily job.

Only replace the generated `## Codex Session Logs` block under
`# Where I'm Leaving Off`. Keep concise topic bullets with outcomes and latest
stopping points. Preserve other headings, frontmatter, links, manual notes, and
existing Daily Codex Summary/Jira Ticket Candidates sections. Missing daily notes
are skipped; their activity is retained for a later run.

## Operations

Collection runs every five minutes on both devices. Summarization runs hourly
only on the laptop. Persistent systemd timers catch up after downtime; scripts
exit after each run. A shared writer lock also covers the integrated daily job.
Use `daily.py` for unattended daily summaries rather than running the old wrapper
in parallel. Do not restart jobs or invoke model runs merely to inspect their state.

A model-call budget bounds each run; completed chunks are cached so a later run
can continue. Record token usage in local `model-usage.jsonl`. If model access,
parsing, or source-attribution validation fails, preserve the existing note and
report the failure. Do not silently substitute another model or weaken validation.
