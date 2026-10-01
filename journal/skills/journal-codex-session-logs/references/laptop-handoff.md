# Laptop continuation and deployment

## Intended deployment

- Desktop: `dcolli23@dylan-lambda`, device `desktop`, collection only.
- Laptop: `dylan.colli@ltmj0ffwl3`, device `laptop`, collection plus Luna High
  summarization and daily-note updates.
- Code: `~/code/codex-skills` on both machines, synced through normal Git pulls.
- Data: `~/journal/codex-activity`, synced through the existing vault sync.
- Python 3.10+ standard library only; Codex CLI handles model authentication.

Laptop deployment is deliberately deferred. The implementation session could not
reach the laptop by hostname or `192.168.1.174`; Dylan asked to leave complete
instructions for a later Codex session on that machine. Do not interpret this
handoff as confirmation that laptop timers, model access, or cross-device sync
have been verified.

## Desktop deployment status from implementation

The desktop config, journal-local skill symlink, and collector service/timer
symlinks were installed. A real collection completed without parse errors; a
no-change replay produced zero new records in the isolated preview. Initial
filtered activity for 2026-09-30 was about 227 KB across 10 sessions. Subsequent
manual collection wrote the actual batches under `~/journal/codex-activity`.

**The desktop timer is not enabled or running yet.** Its existing systemd user
manager fails before these jobs can start: `/run/user/1000` is owned by root,
and `pam_systemd` refuses to set `XDG_RUNTIME_DIR`. `user@1000.service` reports
`Runtime directory '/run/user/1000' is not owned by UID 1000, as it should.`
This host ownership issue was not changed by the implementation. A desktop
session/admin should inspect how that directory is created/mounted, repair it
appropriately, and restore the user manager before running:

```bash
systemctl --user daemon-reload
systemctl --user enable --now codex-activity-collect.timer
systemctl --user start codex-activity-collect.service
systemctl --user list-timers codex-activity-collect.timer --all --no-pager
```

Consider enabling user lingering on the desktop if collection must continue
without a login session, after confirming the user manager is healthy. Until
then, `python3 .../scripts/collect.py` can be run manually; don't mistake old
desktop coverage for an active collector. Laptop deployment can still proceed
independently, using the batches already synced and reporting desktop coverage.

A later session can start with:

> Deploy the journal-codex-session-logs workflow on this laptop using
> ~/code/codex-skills/journal/skills/journal-codex-session-logs/references/laptop-handoff.md.
> Preserve my existing daily/weekly summary setup. Verify vault sync of desktop
> activity, Luna High access, and daily-summary integration before enabling timers.

## Inspect before installing

Read the repository and journal AGENTS.md files. Inspect Git status before pulling
and preserve local changes. Confirm `hostname` is `ltmj0ffwl3`, the real home/vault
paths (corporate home directories may differ from the SSH username), and the
existing `codex-daily-summary.service`/timer and weekly service/timer with
`systemctl --user cat`. Read `SYSTEMD_JOURNAL_SUMMARY_JOBS.md` for those jobs.
Do not copy credentials from the desktop.

Update the skills checkout through its normal Git workflow. Run:

```bash
cd ~/code/codex-skills
python3 -m unittest discover -s journal/skills/journal-codex-session-logs/tests -v
python3 journal/skills/journal-codex-session-logs/scripts/install.py --device laptop
```

This installs config, the new journal-local skill link, and timer/service links,
without starting them. It preserves an existing config on reinstallation.
Configuration lives at `~/.config/codex-activity/config.json`. Review `vault`,
`codex` (absolute executable path), `since` (first imported day), and `writer: true`.
Keep device IDs exactly `laptop` and `desktop`; they partition immutable records.
The installed skill link should resolve to this machine's checkout, not the
other machine's home path. Existing summary skills and journal AGENTS.md should
also point to this machine's tracked sources.

## Verify sync before spending tokens

Obsidian Sync is enabled on the desktop. Its presence alone does not establish
that JSONL/JSON files sync. In Obsidian Sync settings, enable syncing **all other
file types** if needed and ensure `codex-activity` is not excluded, on both devices.
The desktop must have its vault sync running for batches to reach the laptop;
collection itself works without Obsidian running or network access.

On the laptop, verify that these have arrived:

- `codex-activity/devices/desktop.json`
- At least one `codex-activity/YYYY-MM-DD/desktop/<session-id>/*.jsonl`

Compare a specific immutable batch's filename and SHA-256 on both machines when
possible. Do not conclude that sync works merely because the heartbeat arrived.
If the Sync plan/client cannot carry these extensions, stop and resolve transport
rather than enabling incomplete summaries or creating another note writer.

Run the collector manually and confirm a second run reports zero new records
when no session activity has changed:

```bash
python3 journal/skills/journal-codex-session-logs/scripts/collect.py
python3 journal/skills/journal-codex-session-logs/scripts/collect.py
```

## Verify Luna and environment

The hourly and integrated daily services explicitly load
`~/.config/environment.d/bg-ai-gateway.conf`, matching the existing jobs. Preserve
that directive. Check file existence/permissions without printing the key. The
Codex invocation retains the user's provider config and uses saved CLI auth;
it explicitly selects `gpt-6-luna` and `model_reasoning_effort="high"` for session
logs. Provider/model access must be verified on the laptop—desktop access does
not prove gateway access. The normal Slack/journal daily-summary run keeps the
existing CLI default model.

Use a transient user service to run the opt-in, single-call synthetic smoke test
with the same credential environment as the timers (no real journal edits):

```bash
systemd-run --user --wait --pipe --collect \
  -p "EnvironmentFile=$HOME/.config/environment.d/bg-ai-gateway.conf" \
  /usr/bin/python3 "$HOME/code/codex-skills/journal/skills/journal-codex-session-logs/tests/smoke_model.py"
```

If your `codex` executable isn't in the user manager's PATH, add its parent via an
Environment=PATH override to this smoke command, or run it in an authenticated
terminal first and then verify the installed service separately. The real jobs
use the absolute path recorded in config. Never substitute a different model
silently if Luna is unavailable.

Run the hourly service once (without enabling its timer) after choosing a narrow
`since` date and inspecting the available input days:

```bash
systemctl --user daemon-reload
systemctl --user start codex-session-logs.service
journalctl --user-unit codex-session-logs.service -n 60 --no-pager
```

Inspect the affected daily note's `## Codex Session Logs`, source artifacts, and
`~/.local/state/codex-activity/model-usage.jsonl`. The script skips missing notes,
uses at most 40 model calls per run, and caches successful stages. Check that early
accomplishments survive later blockers, unrelated tasks stay separate, and
proposals are not reported as completed work. Repeating an unchanged run should
make no model calls.

## Integrate the daily job and enable timers

Once verified, install the reversible daily-service drop-in and enable the two new
timers:

```bash
python3 journal/skills/journal-codex-session-logs/scripts/install.py \
  --device laptop --integrate-daily --enable
systemctl --user cat codex-daily-summary.service
systemctl --user list-timers 'codex-*' --all --no-pager
```

The drop-in changes only the daily service's ExecStart to `scripts/daily.py` and
preserves explicit EnvironmentFile loading. It leaves the original wrapper and
unit intact. The daily timer's schedule stays unchanged; the weekly job is not
replaced. Do not create a second daily timer.

`daily.py` holds the same lock as the hourly writer, collects local changes,
refreshes session logs, and invokes the existing daily-summary skill for the
previous workday plus closed days affected by late input. It supplies
`CODEX_ACTIVITY_PREPARED=1` and an automation marker to prevent recursion. Run it
manually with `--date YYYY-MM-DD` when an explicit date is needed. Don't manually
run the old wrapper concurrently after integration.

Disable the new timers with `systemctl --user disable --now
codex-activity-collect.timer codex-session-logs.timer` if necessary. To undo daily
integration, remove only the `codex-daily-summary.service.d/session-logs.conf`
drop-in and reload the user manager; do not delete the original unit or wrapper.
Keep vault evidence when troubleshooting. For replays/backfills, follow
[the storage contract](activity-format.md).
