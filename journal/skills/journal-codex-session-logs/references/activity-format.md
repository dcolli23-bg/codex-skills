# Activity records and recovery

## Storage ownership

```text
<vault>/codex-activity/
  devices/desktop.json             # latest collector coverage; desktop-owned
  devices/laptop.json              # latest collector coverage; laptop-owned
  YYYY-MM-DD/
    desktop/<session-id>/<digest>.jsonl
    laptop/<session-id>/<digest>.jsonl
    summaries/<digest>.json        # immutable Luna results, laptop-owned
```

Each JSONL file is published atomically, then the collector advances its local
checkpoint. Each line has `schema: 1`, a stable `id`, `session`, `device`, ISO
`timestamp`, journal-local `day`, `cwd`, `kind`, `text`, and `source_offset`.
Batch names are content hashes. Retrying after a crash can produce overlapping
batches; the laptop deduplicates stable event IDs. Do not edit batches in place.
All summary artifacts retain evidence/session IDs; resolve those against JSONL
records to find the machine, session, original byte offset, and source text.

Model calls use temporary short references instead of these full IDs. Evidence
chunks expose `e1`, `e2`, etc.; daily synthesis exposes `t1`, `t2`, etc. for
chunk-summary topics. Python validates returned references and expands them to
full evidence IDs and derived session IDs before saving an artifact. Synthesis
citations inherit the evidence of their selected chunk topics; they do not imply
that each inherited message independently supports every sentence.

The model receives short session labels for grouping, timestamps, message kinds,
text, and a compact directory-context lookup. Collector schema, device, day, byte
offsets, and full IDs stay outside its input. Synthesis receives topic prose,
session labels, and chunk time ranges. Short references are local to one call;
they are never persistent identifiers or replacements for immutable evidence.

Local state is under `~/.local/state/codex-activity/`:

- `checkpoints.json`: source-file byte offsets, working directories, exclusions.
- `collect.lock`: prevents simultaneous collectors on one device.
- `journal-writer.lock`: serializes hourly and integrated daily writers.
- `rendered-days.json`: input hashes, summary results, reconciliation state, and
  pending normal-daily-summary refreshes.
- `model-usage.jsonl`: model, reasoning, prompt character count, CLI usage events,
  and exit status; no raw prompts or credentials.

Checkpoint/state files are not vault data and should not sync between machines.
The vault records and cached summaries are sufficient to rebuild the view.

## Collection coverage and filtering

The collector reads `~/.codex/sessions/**/*.jsonl` and
`~/.codex/archived_sessions/**/*.jsonl`, using `session_meta`, `turn_context`,
`response_item`, and interruption events. It has been exercised against local
0.153/0.159-era rollout records. This is an internal format, not a guaranteed
public API. New clients with paginated/different storage need an adapter; an
empty collector is not proof that the user had no activity.

- Group by each event timestamp in `America/New_York`, not session creation date.
- Retain genuine user messages and assistant final/commentary messages.
- Remove known injected instruction/environment blocks, developer/system messages,
  reasoning records, and duplicate `event_msg` copies of conversation messages.
- Keep selected test/exit/commit/push outcome lines from tool results; omit full
  commands, source dumps, and long fenced code/output blocks. Long prose is split
  into bounded records, not silently discarded.
- Redact recognizable token/password assignments, bearer tokens and private keys.
  This is best-effort filtering, not a guarantee that arbitrary secrets cannot
  appear in user-authored text. Records have the same private scope as the vault.
- Omit subagent rollouts to avoid inherited-history duplication; parent messages
  and returned tool results are the evidence for delegated work. Work present only
  in a child's transcript is not independently captured in this first version.
- Omit marked `[codex-activity-automation]` sessions and the existing scheduled
  daily/weekly summary prompts. The new Luna and daily invocations also use
  `--ephemeral`, so they do not create source rollouts.
- Resume an incomplete last line next time. Stop at a malformed complete line and
  report its filename/offset rather than silently skipping it.

`since` limits the first activity day imported. The installer defaults to the
local installation day to avoid unexpectedly processing months of history.
To backfill earlier days, lower `since` and move the local checkpoint file aside
while the collector is stopped; leave published batches intact. Stable IDs make
replay safe. Choose a new state directory in a temporary config for a dry run.

## Summary and note consistency

Evidence is divided into bounded per-session chunks. Inputs, model, reasoning,
prompt version, and stage identify cached results. Adding activity normally
reuses previous complete chunks and recomputes only the changing tail. The final
synthesis considers the whole day in one call over compact topic references.
Its input limit is 64,000 characters including the prompt and output schema,
separate from the 24,000-character raw-record chunk limit. If synthesis exceeds
that limit, the run stops with an explicit error, preserves the note and cached
chunks, and requires input-budget/design review. It never recursively compresses
summaries. Closed-day reconciliation uses fresh evidence
chunk prompts; it does not trust a repeatedly rewritten session summary. Chunk
artifacts are never overwritten by synthesis.

There are two useful limits: `max_calls_per_run` (default 40) and
`model_timeout_seconds` (default 600). Exceeding the call budget leaves completed
artifacts cached and resumes on a future run. No model call occurs for unchanged
input. When evidence changes on a closed day, normal daily-summary refresh is
queued for `daily.py`; this keeps Slack calls out of the hourly job.

Generated note text is enclosed by `<!-- codex-session-logs:start -->` and
`<!-- codex-session-logs:end -->`. A legacy unmarked section is replaced by heading
boundaries. Duplicate/broken markers fail instead of guessing. The writer reads
the current file after model calls and checks for changes before an atomic
replacement. Locks coordinate these jobs, not Obsidian itself or an unrelated
manual editor; avoid editing the generated block during an update.

Coverage timestamps state when each collector last scanned, not a transactional
promise that every batch has finished syncing. Heartbeats can arrive before a
batch. Late batches are processed on the next run. Retain the coverage caveat in
the note until sync behavior has been confirmed across both machines.
