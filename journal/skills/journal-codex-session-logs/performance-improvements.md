# Summarization performance improvements

Recorded 2026-10-01. These are proposed experiments, not implemented changes.

## Measured baseline

The isolated prototype used the largest collected session from 2026-09-30:
`01a0f526-6b3c-7ea1-8fec-73f1613f94f7` (Dorkspace workflow and activity journaling).

- 116 records, 54,615 characters of source text, and five input chunks.
- Three matching chunk summaries were reused from prompt version 2; two missing
  chunks were summarized using the compact-reference implementation.
- The synthesis call took 18.23 seconds; the whole prototype took 44.22 seconds.
- Synthesis used 6,813 input tokens and 2,254 output tokens, including 1,689
  reasoning tokens (565 other output tokens).
- Serialized records measured 90,714 characters; the compact model payload
  measured 70,254 characters. Chunking still uses the original record sizes.
- The day's available evidence spanned 12 sessions and 21 chunks at measurement.

These are single-run observations, not general latency guarantees. The prototype
reused some older chunk summaries, so it measures synthesis rather than a fresh
run of the entire session under the current prompt.

Compact source references and one bounded daily synthesis call are already
implemented. Recursive consolidation has been removed. The suggestions below
build on that implementation.

## Proposed improvements, in priority order

- [ ] **Compare Luna medium reasoning with High.** Use exactly the same cached
  inputs and synthesis prompt. Measure latency, input/output/reasoning tokens,
  and quality: factual accuracy, conservative topic grouping, distinction between
  plans and completed work, and useful stopping points. Keep the production
  setting unchanged until the comparison supports a decision.

- [ ] **Summarize ordinary sessions directly.** For sessions that fit the input
  budget, produce the final session summary in one call. Use chunk summaries for
  larger sessions. Verify that the direct path preserves source attribution and
  avoids an unnecessary second call for small sessions.

- [ ] **Size chunks after removing metadata.** Base chunk boundaries on the
  compact model payload, accounting for prompt/schema overhead. Compare chunk
  counts and calls against the current raw-record sizing. Keep stable chunk
  boundaries where possible so small additions preserve cache reuse.

- [ ] **Refresh only changed sessions hourly.** Cache final summaries per session
  and assemble the hourly note in Python. Reserve cross-session synthesis for
  the daily job, where related work and later outcomes need reconciliation.
  Evaluate duplication across sessions and make the scope of stopping points
  clear; a single-session view may lack later work from another conversation.

- [ ] **Process independent chunks concurrently.** Try a small concurrency limit
  and measure elapsed time. This can reduce latency but does not inherently
  reduce token cost. Preserve the shared call budget, completed-result caching,
  failure handling, and single-writer behavior.

## Next experiment

Run only the single-session synthesis at medium reasoning and compare it with
the High result above. Save previews and metrics outside the real journal.
Avoid full-pipeline runs while prototyping speed improvements. Then evaluate
the direct single-call path for small sessions.

For each experiment, record the implementation/prompt version, input snapshot,
cache reuse, reasoning setting, call count, stage timings, token usage, quality
findings, and the decision. Follow [AGENTS.md](AGENTS.md) for prompt-version bumps
when changing production summarization behavior.
