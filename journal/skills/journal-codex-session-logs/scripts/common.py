"""Shared storage, configuration, and locking for journal activity jobs (stdlib only)."""
import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import tempfile
from zoneinfo import ZoneInfo

DEFAULT_CONFIG = Path.home() / '.config/codex-activity/config.json'
VERSION = 1


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def digest(value):
    return hashlib.sha256(encode(value).encode()).hexdigest()


def utcnow():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def timestamp(value):
    parsed = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('Activity timestamps must include a timezone')
    return parsed


def read_json(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def atomic_write(path, text):
    """Publish a complete file on the same filesystem; never expose partial JSONL."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix='.' + path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        if path.exists():
            os.chmod(temp, path.stat().st_mode & 0o777)
        os.replace(temp, path)
        directory = os.open(path.parent, os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def write_json(path, value):
    atomic_write(path, encode(value) + '\n')


@contextlib.contextmanager
def locked(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        yield


class Config:
    """Machine settings are local; no credentials belong in this file."""
    def __init__(self, path=DEFAULT_CONFIG):
        self.path = Path(path)
        data = read_json(self.path)
        if not isinstance(data, dict):
            raise ValueError(f'Missing configuration: {self.path}; run install.py first')
        self.device = data['device']
        if self.device not in ('desktop', 'laptop'):
            raise ValueError('device must be desktop or laptop')
        self.writer = data.get('writer', False)
        if self.writer and self.device != 'laptop':
            raise ValueError('Only the laptop is the journal writer')
        self.vault = Path(data['vault']).expanduser().resolve()
        if not self.vault.is_dir():
            raise ValueError(f'Vault is unavailable: {self.vault}')
        self.codex_home = Path(data.get('codex_home', '~/.codex')).expanduser()
        self.state = Path(data.get('state', '~/.local/state/codex-activity')).expanduser()
        self.activity = self.vault / 'codex-activity'
        self.zone = ZoneInfo(data.get('timezone', 'America/New_York'))
        self.since = dt.date.fromisoformat(data['since'])
        self.codex = data.get('codex', 'codex')
        self.model = data.get('model', 'gpt-6-luna')
        self.reasoning = data.get('reasoning', 'high')
        self.max_calls = int(data.get('max_calls_per_run', 40))
        self.timeout = int(data.get('model_timeout_seconds', 600))
        self.expected_devices = data.get('expected_devices', ['desktop', 'laptop'])

    def today(self):
        return dt.datetime.now(self.zone).date()
