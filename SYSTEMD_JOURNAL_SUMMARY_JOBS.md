# Systemd Journal Summary Jobs

This document describes how to set up Dylan's scheduled Codex journal-summary jobs with user-level systemd timers.

The jobs live outside the journal vault, but they run Codex against `~/journal`:

- daily summary: updates the previous workday's `daily/YYYY-MM-DD.md`
- weekly summary: regenerates `weekly/weekly-summary-YYYY-MM-DD.md` for the previous fully completed Monday-Sunday week

## Design

Use user-level systemd units under:

```text
~/.config/systemd/user/
```

Use wrapper scripts under:

```text
~/.local/bin/
```

Use state/output files under:

```text
~/.local/state/codex-daily-summary/
~/.local/state/codex-weekly-summary/
```

Both services must load the Codex model-provider API key with an explicit systemd `EnvironmentFile=` directive. Do not rely on an interactive shell environment or a one-time `systemctl --user import-environment`, because scheduled timers may run before any login shell has exported the key.

## Prerequisites

1. Codex CLI is installed and runnable as `codex`.
2. Journal-local skills are exposed in the journal vault:

   ```bash
   ln -sfn ~/code/codex-skills/journal/skills/journal-daily-codex-summary ~/journal/.codex/skills/journal-daily-codex-summary
   ln -sfn ~/code/codex-skills/journal/skills/journal-last-week-summary ~/journal/.codex/skills/journal-last-week-summary
   ln -sfn ~/code/codex-skills/journal/AGENTS.md ~/journal/AGENTS.md
   ```

3. The BG AI Gateway API key is stored in a local, non-version-controlled environment file:

   ```bash
   mkdir -p ~/.config/environment.d
   chmod 700 ~/.config/environment.d
   cat > ~/.config/environment.d/bg-ai-gateway.conf <<'ENV'
   BG_AI_GATEWAY_API_KEY=replace-with-real-key
   ENV
   chmod 600 ~/.config/environment.d/bg-ai-gateway.conf
   ```

   Keep this file out of git. Never commit the real key.

## Daily Summary Job

Create the wrapper script:

```bash
cat > ~/.local/bin/run-yesterday-daily-summary <<'EOF_SCRIPT'
#!/usr/bin/env bash
set -euo pipefail

export PATH="$HOME/.local/npm/bin:$PATH"

JOURNAL="$HOME/journal"
TODAY_DOW="$(date +%u)"

case "$TODAY_DOW" in
  1)
    DATE="$(date -d '3 days ago' +%F)"
    ;;
  7)
    DATE="$(date -d '2 days ago' +%F)"
    ;;
  *)
    DATE="$(date -d yesterday +%F)"
    ;;
esac

LOG_DIR="$HOME/.local/state/codex-daily-summary"
LAST_MESSAGE="$LOG_DIR/last-message-${DATE}.md"

mkdir -p "$LOG_DIR"
cd "$JOURNAL"

if [[ ! -f "daily/${DATE}.md" ]]; then
  printf 'No daily note found for %s; skipping daily summary.\n' "$DATE" | tee "$LAST_MESSAGE"
  exit 0
fi

codex exec \
  --full-auto \
  -C "$JOURNAL" \
  -o "$LAST_MESSAGE" \
  "Use the journal-daily-codex-summary skill. This is a scheduled, non-interactive run. Before reading note context, read AGENTS.md and UNKNOWN_ACRONYMS.md. Generate or replace the Daily Codex Summary for ${DATE}. Use Slack plus the journal daily note and directly linked/transcluded notes. If you discover unfamiliar acronyms, shorthand, people, product names, site labels, or domain terms whose meaning is not confirmed by acronyms/ or context, do not ask the user in this run. Instead, create or update top-level UNKNOWN_ACRONYMS.md with concise unresolved entries including the term, date, source note or Slack context, and the question Dylan should answer. Only create or update acronyms/ entries when the meaning is confirmed by the existing glossary, notes, or this prompt. Keep edits scoped to daily/${DATE}.md, acronyms/ entries with confirmed meanings, and UNKNOWN_ACRONYMS.md."
EOF_SCRIPT
chmod +x ~/.local/bin/run-yesterday-daily-summary
```

Create the service:

```bash
cat > ~/.config/systemd/user/codex-daily-summary.service <<'EOF_SERVICE'
[Unit]
Description=Run Codex daily journal summary for previous workday

[Service]
Type=oneshot
EnvironmentFile=%h/.config/environment.d/bg-ai-gateway.conf
ExecStart=%h/.local/bin/run-yesterday-daily-summary
EOF_SERVICE
```

Create the timer:

```bash
cat > ~/.config/systemd/user/codex-daily-summary.timer <<'EOF_TIMER'
[Unit]
Description=Run Codex daily journal summary after first laptop use

[Timer]
OnCalendar=*-*-* 05:00:00
Persistent=true
RandomizedDelaySec=2m
Unit=codex-daily-summary.service

[Install]
WantedBy=timers.target
EOF_TIMER
```

## Weekly Summary Job

Create the wrapper script:

```bash
cat > ~/.local/bin/run-last-week-summary <<'EOF_SCRIPT'
#!/usr/bin/env bash
set -euo pipefail

export PATH="$HOME/.local/npm/bin:$PATH"

JOURNAL="$HOME/journal"
RUN_DATE="$(date +%F)"
LOG_DIR="$HOME/.local/state/codex-weekly-summary"
LAST_MESSAGE="$LOG_DIR/last-message-${RUN_DATE}.md"

mkdir -p "$LOG_DIR"
cd "$JOURNAL"

codex exec \
  --full-auto \
  -C "$JOURNAL" \
  -o "$LAST_MESSAGE" \
  "Use the journal-last-week-summary skill. This is a scheduled, non-interactive run. Before reading note context, read AGENTS.md and UNKNOWN_ACRONYMS.md. Generate or fully regenerate the weekly summary for the previous fully completed Monday-Sunday week. Read the relevant daily notes, directly linked/transcluded notes, and write the result to the correct weekly/weekly-summary-YYYY-MM-DD.md file. If you discover unfamiliar acronyms, shorthand, people, product names, site labels, or domain terms whose meaning is not confirmed by acronyms/ or context, do not ask the user in this run. Instead, create or update top-level UNKNOWN_ACRONYMS.md with concise unresolved entries including the term, source/date context, and the question Dylan should answer. Only create or update acronyms/ entries when the meaning is confirmed by the existing glossary, notes, or this prompt. Keep edits scoped to the weekly summary file, acronyms/ entries with confirmed meanings, and UNKNOWN_ACRONYMS.md."
EOF_SCRIPT
chmod +x ~/.local/bin/run-last-week-summary
```

Create the service:

```bash
cat > ~/.config/systemd/user/codex-weekly-summary.service <<'EOF_SERVICE'
[Unit]
Description=Run Codex weekly journal summary for last week

[Service]
Type=oneshot
EnvironmentFile=%h/.config/environment.d/bg-ai-gateway.conf
ExecStart=%h/.local/bin/run-last-week-summary
EOF_SERVICE
```

Create the timer:

```bash
cat > ~/.config/systemd/user/codex-weekly-summary.timer <<'EOF_TIMER'
[Unit]
Description=Run Codex weekly journal summary every Monday

[Timer]
OnCalendar=Mon *-*-* 09:15:00
Persistent=true
Unit=codex-weekly-summary.service

[Install]
WantedBy=timers.target
EOF_TIMER
```

## Enable Timers

Reload user systemd and enable both timers:

```bash
systemctl --user daemon-reload
systemctl --user enable --now codex-daily-summary.timer
systemctl --user enable --now codex-weekly-summary.timer
```

Check schedule:

```bash
systemctl --user list-timers 'codex-*-summary.timer' --all --no-pager
```

## Verification

The API-key failure mode to guard against is:

```text
Missing environment variable: `BG_AI_GATEWAY_API_KEY`
```

To verify the services do not rely on a shell-imported key, remove the key from the user manager's transient environment and run the services through systemd:

```bash
systemctl --user unset-environment BG_AI_GATEWAY_API_KEY
systemctl --user start codex-weekly-summary.service
systemctl --user start codex-daily-summary.service
```

Then inspect status and logs:

```bash
systemctl --user show codex-weekly-summary.service -p Result -p ExecMainStatus -p ActiveState --no-pager
systemctl --user show codex-daily-summary.service -p Result -p ExecMainStatus -p ActiveState --no-pager
journalctl --user-unit codex-weekly-summary.service -n 100 --no-pager
journalctl --user-unit codex-daily-summary.service -n 100 --no-pager
```

Confirm systemd loaded the `EnvironmentFile=` directive:

```bash
systemctl --user show codex-weekly-summary.service -p EnvironmentFiles --no-pager
systemctl --user show codex-daily-summary.service -p EnvironmentFiles --no-pager
```

Expected output includes:

```text
EnvironmentFiles=/home/dylan.colli@berkshiregrey.com/.config/environment.d/bg-ai-gateway.conf (ignore_errors=no)
```

A successful oneshot service ends as `ActiveState=inactive` with `Result=success` and `ExecMainStatus=0`.

## Troubleshooting

### `Missing environment variable: BG_AI_GATEWAY_API_KEY`

Check that both service files include:

```ini
EnvironmentFile=%h/.config/environment.d/bg-ai-gateway.conf
```

Then run:

```bash
systemctl --user daemon-reload
systemctl --user show codex-daily-summary.service -p EnvironmentFiles --no-pager
systemctl --user show codex-weekly-summary.service -p EnvironmentFiles --no-pager
```

### Timer did not appear to run

Use:

```bash
systemctl --user list-timers 'codex-*-summary.timer' --all --no-pager
journalctl --user-unit codex-daily-summary.timer --no-pager
journalctl --user-unit codex-weekly-summary.timer --no-pager
```

Both timers use `Persistent=true`, so missed runs should fire after the laptop is next awake and the user systemd manager is running.

### Daily job skipped

The daily wrapper intentionally exits successfully if the target daily note is missing:

```text
No daily note found for YYYY-MM-DD; skipping daily summary.
```

This avoids creating empty or misleading daily notes from a scheduled job.

### Codex CLI warning about `--full-auto`

The current scripts use `--full-auto` because that matches the existing setup. If Codex removes that flag, update the wrapper scripts to the replacement non-interactive workspace-write mode recommended by the installed Codex CLI.
