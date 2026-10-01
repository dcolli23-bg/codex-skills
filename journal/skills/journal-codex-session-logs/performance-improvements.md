# Summarization performance improvements

Recorded 2026-10-01. Proposed experiments and measured results are tracked below;
completed experiments do not imply a production setting change.

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

- [x] **Compare Luna medium reasoning with High (single-run prototype).** Use exactly the same cached
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

## Luna medium comparison — 2026-10-01

Used the same five cached chunk summaries, synthesis prompt, and output schema
as the High baseline. No chunk calls were rerun. Prompt: 7,773 characters;
schema: 540 characters; both runs reported 6,813 input tokens and zero cached
input tokens. The current prompt version was 3.

| Metric | High | Medium |
| --- | ---: | ---: |
| Synthesis time | 18.23 s | 15.07 s |
| Model calls | 1 | 1 |
| Output tokens, including reasoning | 2,254 | 1,624 |
| Reasoning tokens | 1,689 | 996 |
| Other output tokens | 565 | 628 |
| Rendered topics | 6 | 8 |

Medium was 3.16 seconds (17%) faster and used 41% fewer reasoning tokens in this
comparison. It retained the main subjects but separated the desktop collector
and installation-guide work into additional topics. Both outputs retained the
inconsistency where a reported idle-lock configuration change ended with
“Discussion only.” Both reflected the session's incomplete view of later laptop
work. This experiment did not establish a general latency improvement or resolve
those quality issues.

Decision: leave production at High for now. Medium is a plausible speed option,
but the extra topics may work against the desired concise morning recap. One run
per setting is insufficient to separate reasoning effects from service latency
and output variability.

Prototype artifacts (local temporary files):

- High: `/tmp/codex-largest-session-prototype/`.
- Medium: `/tmp/codex-largest-session-medium/`, including input snapshot,
  preview, result, metrics, and token usage.
- Input digest: `c9da995f251766184286145aff1fa0ad210ffb30822646b540e86450123ba812`.
- Prompt digest: `f52155fd31f8030cf55bc8bc2b7feef4c5adc42e240ed1bfaf9bd43b15e43c95`.

The real journal was unchanged. Summary timers remained paused for prototyping.

## Next experiments

### Implemented input filter — 2026-10-01

At Dylan's request, prompt version 4 uses only user messages and explicitly
marked assistant final responses. Commentary, tool outcomes, and interruption
events remain collected but do not enter model input or summary cache hashes.
All 26 tests passed, including exclusion and cache-invalidation behavior.

With the same September 30 evidence, the largest session drops from 116 to 69
records and five to three chunks; its compact payload drops from 70,254 to
54,828 characters. Across the day, chunks drop from 21 to 16 and message text
from 176,748 to 138,819 characters. These are offline input measurements; no
new Luna latency or output-quality comparison has been run for this filter.

### Candidates

Evaluate the direct single-call path for small sessions. If considering a
production reasoning change, repeat the paired synthesis comparison on fixed
inputs and review quality before choosing a default. Save previews and metrics
outside the real journal; avoid full-pipeline runs while prototyping speed
improvements.

For each experiment, record the implementation/prompt version, input snapshot,
cache reuse, reasoning setting, call count, stage timings, token usage, quality
findings, and the decision. Follow [AGENTS.md](AGENTS.md) for prompt-version bumps
when changing production summarization behavior.
