"""Behavioral tests using synthetic rollouts and a deterministic model double."""
import datetime as dt
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import collect
from common import Config, read_json, write_json
from daily import previous_workday
import daily
import summarize
from update_note import replace_section, write_note


class ActivityTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.vault = self.root / 'vault'
        (self.vault / 'daily').mkdir(parents=True)
        self.path = self.root / 'config.json'
        write_json(self.path, {'device': 'laptop', 'writer': True, 'vault': str(self.vault),
                              'codex_home': str(self.root / 'codex'), 'state': str(self.root / 'state'),
                              'since': '2026-09-29'})
        self.config = Config(self.path)
        self.rollout = self.config.codex_home / 'sessions/old-session.jsonl'
        self.rollout.parent.mkdir(parents=True)
        self.add('session_meta', {'id': 'session-1', 'cwd': '/work', 'thread_source': 'user'})
        self.calls = []

    def add(self, kind, payload, at='2026-09-30T16:00:00Z', complete=True):
        row = json.dumps({'timestamp': at, 'type': kind, 'payload': payload})
        with self.rollout.open('a') as stream:
            stream.write(row + ('\n' if complete else ''))

    def message(self, text, role='user', at='2026-09-30T16:00:00Z'):
        self.add('response_item', {'type': 'message', 'role': role,
                                  'phase': 'final_answer' if role == 'assistant' else None,
                                  'content': [{'type': 'output_text' if role == 'assistant' else 'input_text', 'text': text}]}, at)

    def records(self, day='2026-09-30'):
        return summarize.load_records(self.config, day)

    def model(self, mode, items):
        self.calls.append((mode, items))
        sessions, evidence = summarize.source_ids(items)
        return {'topics': [{'title': 'Parser work', 'outcome': 'Implemented parsing; tests passed.',
                            'status': 'complete', 'next_step': '', 'sessions': sorted(sessions),
                            'evidence': sorted(evidence)}]}

    def test_incremental_partial_line_and_timezone(self):
        self.message('Started parsing')
        self.add('response_item', {'type': 'message', 'role': 'user', 'content': [
            {'type': 'input_text', 'text': 'Continue tomorrow'}]}, '2026-10-01T03:59:00Z', complete=False)
        self.assertEqual(collect.collect(self.config)['records'], 1)
        self.assertEqual(collect.collect(self.config)['records'], 0)
        with self.rollout.open('a') as stream:
            stream.write('\n')
        self.message('New day', at='2026-10-01T04:01:00Z')
        collect.collect(self.config)
        self.assertEqual(len(self.records()), 2)
        self.assertEqual(len(self.records('2026-10-01')), 1)

    def test_filters_context_reasoning_duplicates_and_secrets(self):
        self.message('# AGENTS.md instructions for /work\n<INSTRUCTIONS>Injected stuff</INSTRUCTIONS>\n<environment_context>meta</environment_context>')
        self.message('<environment_context>meta</environment_context>\nFix the parser')
        self.add('response_item', {'type': 'reasoning', 'summary': [{'text': 'Private reasoning'}]})
        self.add('event_msg', {'type': 'user_message', 'message': 'Fix the parser'})
        self.add('response_item', {'type': 'message', 'role': 'developer', 'content': [{'type': 'input_text', 'text': 'Instructions'}]})
        self.message('Fixed it. API_KEY=topsecret', 'assistant')
        self.add('response_item', {'type': 'function_call_output', 'output': json.dumps({'exit_code': 0, 'output': 'large arbitrary dump\n12 passed in 0.20s'})})
        collect.collect(self.config)
        text = json.dumps(self.records())
        self.assertNotIn('Injected stuff', text)
        self.assertNotIn('Private reasoning', text)
        self.assertNotIn('topsecret', text)
        self.assertNotIn('large arbitrary dump', text)
        self.assertIn('12 passed', text)
        self.assertEqual(sum(r['kind'].startswith('user:') for r in self.records()), 1)

    def test_crash_after_batch_before_checkpoint_is_replay_safe(self):
        self.message('Implement parsing')
        original = collect.write_json
        def crash(path, value):
            if path.name == 'checkpoints.json':
                raise OSError('simulated crash')
            original(path, value)
        with patch.object(collect, 'write_json', side_effect=crash):
            with self.assertRaises(OSError):
                collect.collect(self.config)
        self.message('Tests pass', 'assistant', at='2026-09-30T17:00:00Z')
        collect.collect(self.config)
        self.assertEqual(len(self.records()), 2)  # Overlapping immutable batches deduplicated.

    def test_automation_and_children_excluded(self):
        self.message(collect.AUTOMATION + '\nSummarize this work')
        self.message('Summary generated', 'assistant')
        self.assertEqual(collect.collect(self.config)['records'], 0)
        self.rollout.write_text('')
        self.add('session_meta', {'id': 'child-1', 'source': {'subagent': {}}})
        self.message('Inherited transcript')
        self.assertEqual(collect.collect(self.config)['records'], 0)

    def test_malformed_complete_record_does_not_advance_past_it(self):
        self.message('Valid')
        with self.rollout.open('a') as stream:
            stream.write('not-json\n')
        self.message('Must not silently skip the malformed row')
        result = collect.collect(self.config)
        self.assertEqual(result['errors'], 1)
        self.assertEqual(len(self.records()), 1)
        self.assertEqual(collect.collect(self.config)['errors'], 1)

    def test_missing_note_no_model_and_unchanged_input_no_model(self):
        self.message('Implement parsing')
        collect.collect(self.config)
        summarize.run(self.config, model=self.model)
        self.assertEqual(self.calls, [])
        note = self.vault / 'daily/2026-09-30.md'
        note.write_text('---\ntags: [daily]\n---\n# Where I\'m Leaving Off\n\n- Manual item\n\n## Daily Codex Summary\n\nExisting\n')
        summarize.run(self.config, model=self.model)
        count = len(self.calls)
        summarize.run(self.config, model=self.model)
        self.assertEqual(len(self.calls), count)
        self.assertIn('- Manual item', note.read_text())
        self.assertIn('## Daily Codex Summary\n\nExisting', note.read_text())
        self.assertEqual(note.read_text().count('## Codex Session Logs'), 1)

    def test_late_evidence_preserves_earlier_chunks_and_marks_daily_refresh(self):
        self.message('Morning implementation')
        collect.collect(self.config)
        (self.vault / 'daily/2026-09-30.md').write_text('# Where I\'m Leaving Off\n')
        summarize.run(self.config, model=self.model, reconcile=True)
        original = set((self.config.activity / '2026-09-30/summaries').glob('*.json'))
        self.message('Evening blocker', at='2026-09-30T23:00:00Z')
        collect.collect(self.config)
        summarize.run(self.config, model=self.model, reconcile=True)
        self.assertTrue(original <= set((self.config.activity / '2026-09-30/summaries').glob('*.json')))
        raw = [items for mode, items in self.calls if mode.startswith('Reconcile')][-1]
        self.assertEqual({x['text'] for x in raw}, {'Morning implementation', 'Evening blocker'})
        index = read_json(self.config.state / 'rendered-days.json')
        self.assertTrue(index['2026-09-30']['needs_daily_summary'])

    def test_bad_model_attribution_leaves_note_untouched(self):
        self.message('Implement parsing')
        collect.collect(self.config)
        note = self.vault / 'daily/2026-09-30.md'; note.write_text('Original')
        def bad(mode, items):
            result = self.model(mode, items)
            result['topics'][0]['evidence'] = ['invented-id']
            return result
        with self.assertRaises(ValueError):
            summarize.run(self.config, model=bad)
        self.assertEqual(note.read_text(), 'Original')

    def test_desktop_cannot_write_notes(self):
        data = read_json(self.path); data.update(device='desktop', writer=False); write_json(self.path, data)
        with self.assertRaises(ValueError):
            summarize.run(Config(self.path), model=self.model)
        self.assertEqual(self.calls, [])

    def test_note_structure_code_fence_crlf_and_markers(self):
        original = "---\r\ntitle: Daily\r\n---\r\n```md\r\n## Codex Session Logs\r\n```\r\n# Where I'm Leaving Off\r\n\r\nManual\r\n# Other\r\nKeep\r\n"
        result = replace_section(original, '- Generated')
        self.assertIn('Manual\r\n', result)
        self.assertIn('# Other\r\nKeep\r\n', result)
        self.assertEqual(replace_section(result, '- Generated'), result)
        self.assertIn('```md\r\n## Codex Session Logs\r\n```', result)
        with self.assertRaises(ValueError):
            replace_section(result + '<!-- codex-session-logs:start -->', 'oops')

    def test_daily_date_selection(self):
        self.assertEqual(previous_workday(dt.date(2026, 9, 28)), '2026-09-25')
        self.assertEqual(previous_workday(dt.date(2026, 9, 27)), '2026-09-25')
        self.assertEqual(previous_workday(dt.date(2026, 9, 30)), '2026-09-29')

    def test_explicit_daily_date_does_not_process_unrelated_pending_days(self):
        for day in ['2026-09-29', '2026-09-30']:
            (self.vault / 'daily' / (day + '.md')).write_text('Manual note')
        self.config.state.mkdir()
        write_json(self.config.state / 'rendered-days.json',
                   {'2026-09-29': {'needs_daily_summary': True}, '2026-09-30': {'needs_daily_summary': True}})
        with patch.object(sys, 'argv', ['daily.py', '--date', '2026-09-30']), \
             patch.object(daily, 'Config', return_value=self.config), \
             patch.object(daily, 'collect', return_value={'errors': 0}), \
             patch.object(daily, 'run') as refresh, \
             patch.object(daily.subprocess, 'run') as command:
            command.return_value.returncode = 0
            daily.main()
        self.assertEqual(command.call_count, 1)
        self.assertTrue(all(call.kwargs['dates'] == ['2026-09-30'] for call in refresh.call_args_list))
        index = read_json(self.config.state / 'rendered-days.json')
        self.assertTrue(index['2026-09-29']['needs_daily_summary'])
        self.assertFalse(index['2026-09-30']['needs_daily_summary'])

    def test_new_activity_invalidates_earlier_same_day_reconciliation(self):
        self.config.today = lambda: dt.date(2026, 9, 30)
        self.message('Morning work')
        collect.collect(self.config)
        (self.vault / 'daily/2026-09-30.md').write_text('Manual note')
        summarize.run(self.config, model=self.model, reconcile=True)
        self.message('Afternoon work', at='2026-09-30T19:00:00Z')
        collect.collect(self.config)
        summarize.run(self.config, model=self.model)
        index = read_json(self.config.state / 'rendered-days.json')
        self.assertFalse(index['2026-09-30']['reconciled'])

    def test_archive_move_and_cross_device_duplicates(self):
        self.message('Work shared between machines')
        collect.collect(self.config)
        archive = self.config.codex_home / 'archived_sessions/old-session.jsonl'
        archive.parent.mkdir()
        self.rollout.rename(archive)
        collect.collect(self.config)
        self.assertEqual(len(self.records()), 1)
        record = dict(self.records()[0], device='desktop')
        batch = self.config.activity / '2026-09-30/desktop/session-1/copy.jsonl'
        batch.parent.mkdir(parents=True)
        batch.write_text(json.dumps(record) + '\n')
        self.assertEqual(len(self.records()), 1)
        self.assertEqual(collect.collect(self.config)['records'], 0)

    def test_legacy_summary_prompt_excluded_but_discussion_retained(self):
        self.message('Use the journal-daily-codex-summary skill. This is a scheduled, non-interactive run. Summarize yesterday.')
        self.assertEqual(collect.collect(self.config)['records'], 0)
        self.assertFalse(collect.is_automation('We should improve the journal-daily-codex-summary skill.'))

    def test_long_prose_is_preserved_and_since_filters_event_dates(self):
        self.message('Old activity', at='2026-09-28T12:00:00Z')
        text = 'Useful prose. ' * 3000
        self.message(text)
        collect.collect(self.config)
        records = sorted(self.records(), key=lambda r: int(r['id'].rsplit(':', 1)[1]))
        self.assertEqual(''.join(r['text'] for r in records), text.strip())

    def test_note_with_unmarked_legacy_section_replaced_narrowly(self):
        original = "# Where I'm Leaving Off\nManual\n\n## Codex Session Logs\nOld\n\n## Daily Codex Summary\nKeep\n"
        result = replace_section(original, '- New')
        self.assertNotIn('\nOld\n', result)
        self.assertIn('Manual\n', result)
        self.assertIn('## Daily Codex Summary\nKeep\n', result)
        self.assertEqual(result.count('## Codex Session Logs'), 1)

    def test_call_budget_resumes_from_saved_chunks(self):
        self.config.max_calls = 1
        self.message('Implement parsing')
        collect.collect(self.config)
        (self.vault / 'daily/2026-09-30.md').write_text('Original')
        def limited(mode, items):
            if len(self.calls) >= 1:
                raise summarize.CallBudgetExceeded('budget')
            return self.model(mode, items)
        with self.assertRaises(summarize.CallBudgetExceeded):
            summarize.run(self.config, model=limited)
        self.assertEqual((self.vault / 'daily/2026-09-30.md').read_text(), 'Original')
        old_count = len(self.calls)
        summarize.run(self.config, model=self.model)
        self.assertEqual(len(self.calls) - old_count, 1)  # Cached chunk reused; only synthesis runs.


    def test_model_request_omits_full_ids_and_bookkeeping(self):
        self.message('Implemented parsing')
        self.message('Tests passed', 'assistant')
        collect.collect(self.config)
        records = self.records()
        payload, sources = summarize.prepare_model_input(records)
        prompt, schema, _ = summarize.model_request('Summarize', records)
        for record in records:
            self.assertNotIn(record['id'], prompt + json.dumps(schema))
            self.assertNotIn(record['session'], prompt + json.dumps(schema))
        for field in ('source_offset', 'schema', 'device', 'day'):
            self.assertTrue(all(field not in item for item in payload['items']))
        self.assertEqual(payload['contexts'], {'c1': '/work'})
        self.assertEqual([x['kind'] for x in payload['items']], [r['kind'] for r in records])
        self.assertEqual([x['timestamp'] for x in payload['items']], [r['timestamp'] for r in records])
        topic = {'title': 'Parser', 'outcome': 'Tests passed.', 'status': 'complete',
                 'next_step': '', 'sources': ['e2', 'e2']}
        result = summarize.expand_sources({'topics': [topic]}, sources)
        self.assertEqual(result['topics'][0]['evidence'], [records[1]['id']])
        self.assertEqual(result['topics'][0]['sessions'], ['session-1'])

    def test_synthesis_refs_expand_only_selected_topics(self):
        def topic(session, evidence):
            return {'title': 'Work', 'outcome': 'Implemented.', 'status': 'complete',
                    'next_step': '', 'sessions': [session], 'evidence': evidence}
        summaries = [{'topics': [topic('session-a', ['a1', 'a2']), topic('session-b', ['b1'])],
                      'period': {'start': '2026-09-30T12:00:00Z', 'end': '2026-09-30T13:00:00Z'}},
                     {'topics': [topic('session-a', ['a2', 'a3'])]}]
        payload, sources = summarize.prepare_model_input(summaries)
        self.assertEqual([t['sessions'] for t in payload['items']], [['s1'], ['s2'], ['s1']])
        self.assertEqual(payload['items'][0]['period'], summaries[0]['period'])
        output = {'topics': [{'title': 'Work', 'outcome': 'Implemented.', 'status': 'complete',
                              'next_step': '', 'sources': ['t1', 't3']}]}
        result = summarize.expand_sources(output, sources)['topics'][0]
        self.assertEqual(result['sessions'], ['session-a'])
        self.assertEqual(result['evidence'], ['a1', 'a2', 'a3'])

    def test_invalid_compact_citations_preserve_note(self):
        self.message('Implement parsing')
        collect.collect(self.config)
        note = self.vault / 'daily/2026-09-30.md'
        note.write_text('Keep this note')
        for refs in ([], ['e999'], ['session-1'], [123], 'e1'):
            def invalid(mode, items):
                _, sources = summarize.prepare_model_input(items)
                return summarize.expand_sources({'topics': [{
                    'title': 'Work', 'outcome': 'Done.', 'status': 'complete',
                    'next_step': '', 'sources': refs}]}, sources)
            with self.subTest(refs=refs), self.assertRaises(ValueError):
                summarize.run(self.config, model=invalid)
            self.assertEqual(note.read_text(), 'Keep this note')

    def test_large_provenance_uses_one_compact_synthesis(self):
        self.message('Implement parsing')
        collect.collect(self.config)
        note = self.vault / 'daily/2026-09-30.md'
        note.write_text('Manual note')
        records = [dict(self.records()[0], id=f'{i:064x}:0', session=f'session-{i // 200}')
                   for i in range(400)]
        with patch.object(summarize, 'load_records', return_value=records):
            summarize.run(self.config, model=self.model)
            synthesis = [(mode, items) for mode, items in self.calls if mode.startswith('Synthesize')]
            self.assertEqual(len(synthesis), 1)
            self.assertFalse(any(mode.startswith('Consolidate') for mode, _ in self.calls))
            self.assertGreater(len(summarize.encode(synthesis[0][1])), 24000)
            prompt, schema, _ = summarize.model_request(*synthesis[0])
            self.assertLess(len(prompt) + len(summarize.encode(schema)), summarize.SYNTHESIS_BUDGET_CHARS)
            count = len(self.calls)
            summarize.run(self.config, model=self.model)
            self.assertEqual(len(self.calls), count)
        result = read_json(self.config.state / 'rendered-days.json')['2026-09-30']['result']
        self.assertEqual(len(result['topics'][0]['evidence']), 400)
        self.assertIn('**Where I left off:**', note.read_text())

    def test_synthesis_limit_preserves_note_and_cached_chunks(self):
        self.message('Implement parsing')
        collect.collect(self.config)
        note = self.vault / 'daily/2026-09-30.md'
        note.write_text('Manual note')
        with patch.object(summarize, 'SYNTHESIS_BUDGET_CHARS', 1):
            with self.assertRaisesRegex(RuntimeError, 'no consolidation attempted'):
                summarize.run(self.config, model=self.model)
        self.assertEqual(note.read_text(), 'Manual note')
        self.assertEqual(len(self.calls), 1)
        summarize.run(self.config, model=self.model)
        self.assertEqual(len(self.calls), 2)
        self.assertTrue(self.calls[-1][0].startswith('Synthesize'))


    def test_only_user_messages_and_explicit_finals_reach_model(self):
        self.message('Fix the parser')
        self.message('Implemented the parser', 'assistant')
        collect.collect(self.config)
        records = self.records()
        omitted = [dict(records[1], id=f'excluded-{i}', kind=kind, text=f'OMIT-{kind}')
                   for i, kind in enumerate(['assistant:commentary', 'assistant:message',
                                             'tool_outcome', 'interrupted'])]
        final = dict(records[1], id='alternate-final', kind='assistant:final')
        all_records = records + omitted + [final]
        payload, sources = summarize.prepare_model_input(all_records)
        self.assertEqual([x['text'] for x in payload['items']],
                         ['Fix the parser', 'Implemented the parser', 'Implemented the parser'])
        self.assertEqual({e for source in sources.values() for e in source['evidence']},
                         {r['id'] for r in records + [final]})
        summarize.build_summary(self.config, '2026-09-30', all_records, self.model)
        raw_calls = [items for mode, items in self.calls if mode.startswith('Summarize')]
        self.assertEqual(len(raw_calls), 1)
        self.assertEqual(raw_calls[0], records + [final])

    def test_excluded_activity_does_not_invalidate_summary(self):
        self.message('Fix the parser')
        collect.collect(self.config)
        note = self.vault / 'daily/2026-09-30.md'
        note.write_text('Manual note')
        summarize.run(self.config, model=self.model)
        count = len(self.calls)
        self.add('response_item', {'type': 'message', 'role': 'assistant', 'phase': 'commentary',
                                  'content': [{'type': 'output_text', 'text': 'Running checks'}]})
        self.add('response_item', {'type': 'function_call_output', 'output': '12 passed'})
        self.add('event_msg', {'type': 'turn_aborted'})
        collect.collect(self.config)
        self.assertEqual(len(self.records()), 4)
        summarize.run(self.config, model=self.model)
        self.assertEqual(len(self.calls), count)
        self.message('Implemented parsing; tests passed', 'assistant')
        collect.collect(self.config)
        summarize.run(self.config, model=self.model)
        self.assertGreater(len(self.calls), count)

    def test_excluded_only_input_makes_no_model_call(self):
        model = summarize.CodexModel(self.config)
        with patch.object(summarize.subprocess, 'Popen') as process:
            result = model('Summarize', [{'kind': 'assistant:commentary', 'text': 'Checking'}])
        self.assertEqual(result, {'topics': []})
        self.assertEqual(model.calls, 0)
        process.assert_not_called()


if __name__ == '__main__':
    unittest.main()
