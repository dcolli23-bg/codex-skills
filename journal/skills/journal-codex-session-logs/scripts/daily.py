#!/usr/bin/env python3
"""Serialize session-log refresh and the existing daily-summary skill on the laptop."""
import argparse
import datetime as dt
import os
from pathlib import Path
import subprocess
import sys

from collect import AUTOMATION, collect
from common import Config, DEFAULT_CONFIG, locked, read_json, write_json
from summarize import run


def previous_workday(today):
    day = today - dt.timedelta(days=1)
    while day.weekday() >= 5:
        day -= dt.timedelta(days=1)
    return day.isoformat()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=DEFAULT_CONFIG)
    parser.add_argument('--date', help='Explicit YYYY-MM-DD instead of previous workday')
    args = parser.parse_args()
    config = Config(args.config)
    if not config.writer:
        raise ValueError('Daily-note updates run only on the laptop')
    with locked(config.state / 'journal-writer.lock'):
        stats = collect(config)
        if stats['errors']:
            raise RuntimeError('Collector reported errors; inspect the collector service log')
        run(config, dates=[args.date] if args.date else None, reconcile=bool(args.date), lock=False)
        index_path = config.state / 'rendered-days.json'
        index = read_json(index_path, {})
        dates = {args.date or previous_workday(config.today())}
        if not args.date:
            dates.update(day for day, value in index.items() if value.get('needs_daily_summary'))
        for day in sorted(dates):
            dt.date.fromisoformat(day)
            if not (config.vault / 'daily' / (day + '.md')).exists():
                continue
            run(config, dates=[day], reconcile=True, lock=False)
            prompt = (AUTOMATION + '\nUse the journal-daily-codex-summary skill. '
                      f'This is a scheduled, non-interactive run for the explicit target date {day}. '
                      'Session logs were already refreshed by the outer job; do not run this pipeline again. '
                      'Read AGENTS.md and UNKNOWN_ACRONYMS.md before note context. '
                      'Combine Slack, the daily note, directly linked notes, and Codex Session Logs. '
                      'Only replace Daily Codex Summary and Jira Ticket Candidates for this date. '
                      'Preserve the session-log section and all user-written content. '
                      'Record unresolved terminology in UNKNOWN_ACRONYMS.md without asking questions; '
                      'only update acronyms/ for confirmed meanings. Do not create Jira tickets.')
            out = config.state / ('daily-last-message-' + day + '.md')
            environment = dict(os.environ, CODEX_ACTIVITY_PREPARED='1')
            result = subprocess.run([config.codex, 'exec', '--ephemeral', '--approve-for-me',
                                     '-C', str(config.vault), '-o', str(out), prompt], env=environment)
            if result.returncode:
                raise RuntimeError(f'Daily summary failed for {day} (exit {result.returncode})')
            index = read_json(index_path, {})
            if day in index:
                index[day]['needs_daily_summary'] = False
                write_json(index_path, index)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, RuntimeError, OSError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
