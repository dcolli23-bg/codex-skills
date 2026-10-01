#!/usr/bin/env python3
"""Incrementally extract timestamped conversation evidence; never invoke a model."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import sys

from common import Config, DEFAULT_CONFIG, VERSION, atomic_write, digest, encode, locked, read_json, timestamp, utcnow, write_json

AUTOMATION = '[codex-activity-automation]'
AUTO_SKILLS = ('journal-daily-codex-summary', 'journal-last-week-summary')
BLOCKS = ('INSTRUCTIONS', 'environment_context', 'skills_instructions', 'permissions_instructions',
          'collaboration_mode', 'system_reminder', 'environment', 'user_instructions')
SECRET = re.compile(r'(?i)((?:api[_-]?key|access[_-]?token|password|secret)\s*[=:]\s*)[^\s,;]+')


def clean_text(text):
    """Remove known injected context, bulky code, and obvious credentials, retaining prose."""
    for tag in BLOCKS:
        text = re.sub(r'<' + tag + r'\b[^>]*>.*?</' + tag + r'>', '', text, flags=re.S | re.I)
    text = re.sub(r'^# AGENTS\.md instructions for [^\n]*\n?', '', text, flags=re.M)
    text = re.sub(r'-----BEGIN [^-]*PRIVATE KEY-----.*?-----END [^-]*PRIVATE KEY-----',
                  '[private key omitted]', text, flags=re.S)
    text = re.sub(r'(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+', 'Bearer [redacted]', text)
    text = re.sub(r'\b(?:sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,})\b', '[redacted]', text)
    text = SECRET.sub(r'\1[redacted]', text)
    text = re.sub(r'```[^\n]*\n(.*?)```',
                  lambda m: '[long code/output block omitted]' if len(m.group(1)) > 2000 else m.group(0),
                  text, flags=re.S)
    return text.strip()


def message_text(payload):
    return '\n'.join(x.get('text', '') for x in payload.get('content', [])
                     if isinstance(x, dict) and x.get('type') in ('input_text', 'output_text', 'text'))


def is_automation(text):
    # Only inspect genuine user messages, not embedded skill catalogs or assistant examples.
    return (text.startswith(AUTOMATION) or
            (text.startswith('Use ') and 'scheduled, non-interactive run' in text and
             any(s in text[:200] for s in AUTO_SKILLS)))


def metadata(path):
    with path.open('rb') as stream:
        raw = stream.readline()
    try:
        row = json.loads(raw)
    except (ValueError, UnicodeError):
        return None
    return row.get('payload') if row.get('type') == 'session_meta' else None


def tool_evidence(output):
    """Keep outcome lines, not full tool dumps, patches, or shell commands."""
    if isinstance(output, dict):
        output = encode(output)
    if not isinstance(output, str):
        return ''
    try:
        obj = json.loads(output)
        if isinstance(obj, dict):
            output = ('exit_code=' + str(obj.get('exit_code')) + '\n' + str(obj.get('output', '')))
    except ValueError:
        pass
    lines = [line[:300] for line in output.splitlines() if re.search(
        r'(?i)(exit.code[=: ]|process exited with code|\b\d+ (?:passed|failed|errors?)\b|'
        r'^FAILED |^ERROR |^fatal:|^error:|^To (?:github|git@)|-> (?:main|master|devel)|'
        r'^\[[^\]]+ [a-f0-9]{7,}\]|^All checks passed|^Skill is valid)', line)]
    return clean_text('\n'.join(lines[-10:]))[:2000]


def extract(row):
    p = row.get('payload', {})
    if row.get('type') == 'response_item':
        if p.get('type') == 'message' and p.get('role') in ('user', 'assistant'):
            if p.get('role') == 'assistant' and p.get('phase') not in (None, 'final', 'final_answer', 'commentary'):
                return None
            text = clean_text(message_text(p))
            # Compaction summaries are derived context, not new daily activity.
            if text.startswith(('The user requests that you create a detailed summary',
                                'This session is being continued from a previous conversation')):
                return None
            return (p['role'] + ':' + (p.get('phase') or 'message'), text) if text else None
        if p.get('type') in ('function_call_output', 'custom_tool_call_output'):
            text = tool_evidence(p.get('output', ''))
            return ('tool_outcome', text) if text else None
    if row.get('type') == 'event_msg' and p.get('type') == 'turn_aborted':
        return ('interrupted', 'The turn was interrupted; completion is not established.')
    # event_msg duplicates of user/assistant messages are deliberately not collected.
    return None


def collect(config):
    counts = {'records': 0, 'bytes': 0, 'batches': 0, 'errors': 0}
    with locked(config.state / 'collect.lock'):
        checkpoint_path = config.state / 'checkpoints.json'
        checkpoints = read_json(checkpoint_path, {})
        paths = []
        for dirname in ('sessions', 'archived_sessions'):
            paths.extend((config.codex_home / dirname).rglob('*.jsonl'))
        for path in sorted(paths):
            meta = metadata(path)
            if not meta:
                continue
            sid = meta.get('id') or meta.get('session_id')
            if not sid or not re.fullmatch(r'[a-zA-Z0-9_-]+', sid):
                counts['errors'] += 1
                continue
            # Child work is reported through its parent; avoid duplicate inherited context.
            if meta.get('thread_source') == 'subagent' or isinstance(meta.get('source'), dict):
                continue
            stat = path.stat()
            checkpoint_key = str(path.relative_to(config.codex_home))
            cp = checkpoints.get(checkpoint_key, {})
            if cp.get('excluded'):
                continue
            offset = cp.get('offset', 0)
            if stat.st_size < offset:
                offset = 0  # Rewritten/truncated rollout: replay; IDs make this idempotent.
            if stat.st_size == offset:
                continue
            groups = defaultdict(list)
            excluded = False
            cwd = cp.get('cwd', meta.get('cwd', ''))
            try:
                with path.open('rb') as stream:
                    stream.seek(offset)
                    while True:
                        start = stream.tell()
                        line = stream.readline()
                        if not line or not line.endswith(b'\n'):
                            offset = start  # Active partial line is retried on the next run.
                            break
                        row = json.loads(line)  # Malformed complete lines stop this file, never skip.
                        if row.get('type') == 'turn_context':
                            cwd = row.get('payload', {}).get('cwd', cwd)
                        item = extract(row)
                        if item:
                            kind, text = item
                            if kind.startswith('user:') and is_automation(text):
                                excluded = True
                                groups.clear()
                                offset = stream.tell()
                                break
                            when = timestamp(row['timestamp'])
                            day = when.astimezone(config.zone).date()
                            if day >= config.since:
                                event_id = hashlib.sha256(sid.encode() + line).hexdigest()
                                # Preserve long prose in bounded parts rather than dropping its tail.
                                for part, pos in enumerate(range(0, len(text), 12000)):
                                    record = {'schema': VERSION, 'id': event_id + ':' + str(part),
                                              'session': sid, 'device': config.device, 'timestamp': when.isoformat(),
                                              'day': day.isoformat(), 'cwd': cwd, 'kind': kind,
                                              'text': text[pos:pos + 12000], 'source_offset': start}
                                    groups[day.isoformat()].append(record)
                        offset = stream.tell()
            except (ValueError, KeyError, UnicodeError) as error:
                counts['errors'] += 1
                print(f'Cannot parse {path.name} at offset {start}: {type(error).__name__}', file=sys.stderr)
                offset = start
            for day, records in groups.items():
                target = config.activity / day / config.device / sid / (digest(records) + '.jsonl')
                data = ''.join(encode(r) + '\n' for r in records)
                if not target.exists():
                    atomic_write(target, data)
                    counts['batches'] += 1
                    counts['records'] += len(records)
                    counts['bytes'] += len(data.encode())
            # Publish batches before the checkpoint. A crash can replay, but never lose records.
            checkpoints[checkpoint_key] = {'offset': offset, 'cwd': cwd, 'excluded': excluded}
            write_json(checkpoint_path, checkpoints)
        write_json(config.activity / 'devices' / (config.device + '.json'),
                   {'schema': VERSION, 'device': config.device, 'collected_through': utcnow(),
                    'since': config.since.isoformat(), 'errors': counts['errors']})
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    result = collect(Config(args.config))
    print(encode(result))
    return 1 if result['errors'] else 0


if __name__ == '__main__':
    sys.exit(main())
