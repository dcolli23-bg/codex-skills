#!/usr/bin/env python3
"""Install this machine's local config, journal skill link, and systemd units."""
import argparse
import datetime as dt
import json
from pathlib import Path
import shutil
import socket
import subprocess
from zoneinfo import ZoneInfo

from common import DEFAULT_CONFIG, atomic_write, write_json

REPO = Path(__file__).resolve().parents[4]
SKILL = Path(__file__).resolve().parent.parent


def link(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_symlink():
        if destination.resolve() == source.resolve():
            return
        raise ValueError(f'Conflicting symlink: {destination}; inspect before replacing')
    if destination.exists():
        raise ValueError(f'Existing file at {destination}; inspect before replacing')
    destination.symlink_to(source)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device', required=True, choices=['desktop', 'laptop'])
    parser.add_argument('--vault', type=Path, default=Path.home() / 'journal')
    parser.add_argument('--since', help='First local activity day to import; defaults to today')
    parser.add_argument('--enable', action='store_true', help='Reload systemd and enable/start the appropriate timers')
    parser.add_argument('--integrate-daily', action='store_true', help='Laptop: replace daily service ExecStart via a reversible drop-in')
    args = parser.parse_args()
    expected = {'desktop': 'dylan-lambda', 'laptop': 'ltmj0ffwl3'}[args.device]
    if socket.gethostname().split('.')[0].lower() != expected:
        raise ValueError(f'{args.device} installation belongs on {expected}')
    if args.integrate_daily and args.device != 'laptop':
        raise ValueError('Daily integration is laptop-only')
    if REPO != Path.home() / 'code/codex-skills':
        raise ValueError('Install this repository at ~/code/codex-skills for the systemd templates')
    if not args.vault.expanduser().is_dir():
        raise ValueError('Vault directory does not exist')
    config = {'device': args.device, 'writer': args.device == 'laptop',
              'vault': str(args.vault.expanduser().resolve()), 'timezone': 'America/New_York',
              'since': args.since or dt.datetime.now(ZoneInfo('America/New_York')).date().isoformat(),
              'codex': shutil.which('codex') or str(Path.home() / '.local/bin/codex'),
              'model': 'gpt-6-luna', 'reasoning': 'high', 'expected_devices': ['desktop', 'laptop'],
              'max_calls_per_run': 40, 'model_timeout_seconds': 600}
    dt.date.fromisoformat(config['since'])
    if DEFAULT_CONFIG.exists():
        existing = json.loads(DEFAULT_CONFIG.read_text())
        if any(existing[k] != config[k] for k in ('device', 'writer', 'vault')):
            raise ValueError('Existing config differs; edit explicitly rather than silently replacing it')
        print('Keeping existing config, including its original since date.')
    else:
        write_json(DEFAULT_CONFIG, config)
    link(SKILL, args.vault / '.codex/skills/journal-codex-session-logs')
    units = Path.home() / '.config/systemd/user'
    names = ['codex-activity-collect']
    if args.device == 'laptop':
        names.append('codex-session-logs')
    for name in names:
        for extension in ['service', 'timer']:
            filename = name + '.' + extension
            link(REPO / 'journal/systemd' / filename, units / filename)
    if args.integrate_daily:
        if not (units / 'codex-daily-summary.service').exists():
            raise ValueError('Install the existing daily-summary service before integrating it')
        target = units / 'codex-daily-summary.service.d/session-logs.conf'
        content = ('[Service]\nEnvironmentFile=%h/.config/environment.d/bg-ai-gateway.conf\n'
                   'ExecStart=\nExecStart=/usr/bin/python3 %h/code/codex-skills/journal/skills/'
                   'journal-codex-session-logs/scripts/daily.py\nTimeoutStartSec=3h\n')
        if target.exists() and target.read_text() != content:
            raise ValueError('Existing daily integration differs; inspect before replacing')
        atomic_write(target, content)
    if args.enable:
        subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True)
        subprocess.run(['systemctl', '--user', 'enable', '--now'] + [name + '.timer' for name in names], check=True)
    print('Installed ' + args.device + ' config and units. Vault sync must include codex-activity JSON/JSONL files.')


if __name__ == '__main__':
    main()
