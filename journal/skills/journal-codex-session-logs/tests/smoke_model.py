"""Opt-in live Luna smoke check with synthetic evidence; never edits the real vault."""
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from common import Config, write_json
from summarize import CodexModel, validate

with tempfile.TemporaryDirectory(prefix='codex-activity-smoke-') as directory:
    root = Path(directory)
    (root / 'vault').mkdir()
    (root / 'state').mkdir()
    write_json(root / 'config.json', {'device': 'laptop', 'writer': True,
                                    'vault': str(root / 'vault'), 'state': str(root / 'state'),
                                    'since': '2026-09-30', 'max_calls_per_run': 1})
    config = Config(root / 'config.json')
    evidence = [{'id': 'sample-1', 'session': 'synthetic-session', 'timestamp': '2026-09-30T14:00:00Z',
                 'kind': 'user:message', 'text': 'Fix the CSV date parser.'},
                {'id': 'sample-2', 'session': 'synthetic-session', 'timestamp': '2026-09-30T15:00:00Z',
                 'kind': 'assistant:final_answer', 'text': 'Updated the date parser; 12 tests passed. Changes are not committed yet.'}]
    result = CodexModel(config)('Summarize this evidence chunk', evidence)
    print('Synthetic result:', result)
    print((root / 'state/model-usage.jsonl').read_text())
    validate(result, {'synthetic-session'}, {'sample-1', 'sample-2'})
    if not result['topics']:
        raise AssertionError('Luna omitted the substantive synthetic task')
    print('Live Luna High structured-output check passed.')
