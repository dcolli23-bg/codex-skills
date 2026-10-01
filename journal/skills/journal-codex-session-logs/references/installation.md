# Install Codex session journaling on desktop and laptop

## Machine roles and prerequisites

- Desktop: `dcolli23@dylan-lambda`, device `desktop`, collection only.
- Laptop: `dylan.colli@ltmj0ffwl3`, device `laptop`, collection plus Luna High
  summarization and daily-note updates. Only the laptop writes notes.
- Code: `~/code/codex-skills` on both machines, updated through normal Git pulls.
- Data: `~/journal/codex-activity`, transported by the existing vault sync.
- Python 3.10+ standard library only; no venv or Python SDK is required.
- Laptop model access uses the installed Codex CLI and local authentication.
  Do not copy credentials between machines. Collection needs no model credentials.

## Inspect and install on each machine

Read the repository and journal AGENTS.md files. Inspect Git status before pulling
and preserve local changes. Update the checkout through its normal Git workflow.
Confirm the hostname and actual home/vault paths; corporate home directories may
differ from the SSH username. The installer requires the checkout at
`~/code/codex-skills` and checks the hostname for the chosen device.

Confirm the systemd user manager is available with `systemctl --user status`.
On the laptop, inspect the existing daily and weekly services and timers:

```bash
systemctl --user cat codex-daily-summary.service codex-daily-summary.timer \
  codex-weekly-summary.service codex-weekly-summary.timer
```

Use [the summary-job setup](../../../../SYSTEMD_JOURNAL_SUMMARY_JOBS.md) to install
those existing jobs, their journal-local skills, and the credential environment
file if absent. Preserve their schedules and explicit EnvironmentFile loading.

From the checkout, validate the implementation and install the current device:

```bash
cd ~/code/codex-skills
python3 -m unittest discover -s journal/skills/journal-codex-session-logs/tests -v
```

Desktop:

```bash
python3 journal/skills/journal-codex-session-logs/scripts/install.py --device desktop
```

Laptop:

```bash
python3 journal/skills/journal-codex-session-logs/scripts/install.py --device laptop
```

The installer creates config, the journal-local skill symlink, and service/timer
links without starting them. Existing config is preserved on reinstallation.
Use `--vault PATH` for a different vault and `--since YYYY-MM-DD` to select the
first imported day on a fresh installation; the default is today. Keep the first
run narrow. For an existing config or historical backfill, follow
[the storage contract](activity-format.md).

Review `~/.config/codex-activity/config.json`: `vault`, `since`, and device ID;
on the laptop also check the absolute `codex` executable path. Device IDs must
remain `desktop` and `laptop`, with `writer: false` on desktop and `writer: true`
on laptop. Config and `~/.local/state/codex-activity/` stay local and outside Git
and vault sync.

Verify the installed skill link resolves to this machine's checkout:

```bash
readlink -f ~/journal/.codex/skills/journal-codex-session-logs
```

Existing summary skills and journal AGENTS.md should also resolve to this
machine's tracked sources, using the symlinks documented in repository AGENTS.md.
All remaining Python commands below run from `~/code/codex-skills`.

## Verify collection on each machine

Run the collector manually and confirm a second run reports zero new records
when no session activity has changed:

```bash
python3 journal/skills/journal-codex-session-logs/scripts/collect.py
python3 journal/skills/journal-codex-session-logs/scripts/collect.py
```

Inspect reported errors and the device's batches under `~/journal/codex-activity`.
Collection works without Obsidian running or network access. An empty result
alone does not establish that collection is working; compare with known local
session activity and the configured import start date.

## Desktop: enable collection

After local collection and the user manager are verified:

```bash
systemctl --user daemon-reload
systemctl --user start codex-activity-collect.service
journalctl --user-unit codex-activity-collect.service -n 60 --no-pager
systemctl --user enable --now codex-activity-collect.timer
systemctl --user list-timers codex-activity-collect.timer --all --no-pager
```

Collection runs every five minutes. Consider user lingering if it must continue
without a login session, after confirming the user manager is healthy.

### User-manager troubleshooting

If systemd reports that `/run/user/<uid>` is not owned by the expected UID, or
`pam_systemd` refuses to set `XDG_RUNTIME_DIR`, have a host session/admin inspect
how the runtime directory is created or mounted and repair its ownership/lifecycle.
Restore the user manager before enabling timers. Manual collection remains
available; old batches or coverage timestamps do not prove a timer is running.

## Configure and verify cross-device sync

On **both desktop and laptop**, open the journal vault in Obsidian and configure
**Settings → Sync → Selective sync → Sync all other types**. Enable this option
so the `.jsonl` activity batches and `.json` metadata/summary artifacts can sync.
Ensure `codex-activity` is not excluded. This is a required setup step; changing
the setting on one machine does not configure the other, and the installer does
not change Obsidian settings.

Keep Obsidian running with the journal vault open on both machines. Locking the
desktop normally does not stop sync, but closing Obsidian, logging out of its
desktop session, or suspending the machine can. Collection itself works without
Obsidian running or network access; successful collection does not prove upload.

### Configure the desktop remotely with Remmina

When working over SSH without physical desktop access, use the existing desktop
session through VNC. `dylan-lambda` already has x11vnc configured on port 5900;
confirm it is still running before relying on this setup. No additional server
installation or Obsidian restart is needed.

On the laptop, leave this SSH tunnel running:

```bash
ssh -N -L 127.0.0.1:5901:localhost:5900 dcolli23@dylan-lambda
```

In Remmina, select **VNC**, connect to **localhost:5901**, and use the existing
VNC password (which may differ from the Linux login password). Unlock the desktop
if necessary, open Obsidian, and enable the Sync option above. Once syncing
finishes, disconnect Remmina and stop the SSH tunnel; leave Obsidian running in
the desktop session so later batches continue syncing. Launching Obsidian through
SSH X forwarding instead ties that app instance to the SSH connection.

### Verify arrival on the laptop

Check the laptop's filesystem directly: Obsidian's file explorer may hide
unsupported types even when they have synced. Verify that these have arrived:

- `codex-activity/devices/desktop.json`
- At least one `codex-activity/YYYY-MM-DD/desktop/<session-id>/*.jsonl`

Compare a specific immutable batch's filename and SHA-256 on both machines when
possible. Do not conclude that sync works merely because the heartbeat arrived.
If the Sync plan/client cannot carry these extensions, stop and resolve transport
rather than enabling incomplete summaries or creating another note writer.
If Dylan explicitly defers sync verification, proceed with the authorized local
deployment and preserve the coverage caveat; do not claim cross-device completeness.

## Laptop: verify Luna and note updates

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

## Laptop: integrate the daily job and enable timers

Once verified, install the reversible daily-service drop-in, reload systemd, and
inspect the effective daily service before enabling the two new timers:

```bash
python3 journal/skills/journal-codex-session-logs/scripts/install.py \
  --device laptop --integrate-daily
systemctl --user daemon-reload
systemctl --user cat codex-daily-summary.service
systemctl --user enable --now codex-activity-collect.timer codex-session-logs.timer
systemctl --user list-timers 'codex-*' --all --no-pager
```

The drop-in sets the daily service's ExecStart to `scripts/daily.py`, allows a
three-hour startup timeout, and preserves explicit EnvironmentFile loading. It
leaves the original wrapper and unit intact. The daily timer's schedule stays
unchanged; the weekly job is not
replaced. Do not create a second daily timer.

`daily.py` holds the same lock as the hourly writer, collects local changes,
refreshes session logs, and invokes the existing daily-summary skill for the
previous workday plus closed days affected by late input. It supplies
`CODEX_ACTIVITY_PREPARED=1` and an automation marker to prevent recursion. Run it
manually with `--date YYYY-MM-DD` when an explicit date is needed. Don't manually
run the old wrapper concurrently after integration.

## Disable or undo integration

On the desktop, disable collection with
`systemctl --user disable --now codex-activity-collect.timer`.

On the laptop, disable the new timers with `systemctl --user disable --now
codex-activity-collect.timer codex-session-logs.timer` if necessary. To undo daily
integration, remove only the `codex-daily-summary.service.d/session-logs.conf`
drop-in and reload the user manager; do not delete the original unit or wrapper.
Keep vault evidence when troubleshooting. For replays/backfills, follow
[the storage contract](activity-format.md).
