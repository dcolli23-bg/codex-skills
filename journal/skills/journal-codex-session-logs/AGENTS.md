# Journal Codex Session Logs Maintenance

## Summary cache versioning

Increment `PROMPT_VERSION` in `scripts/summarize.py` in the same change whenever
you change model-facing summarization instructions or the meaning/structure of
model output. This includes `RULES`, generated model instructions, chunk and
synthesis prompts, and the output schema or semantic validation contract.

The version participates in both summary-artifact cache keys and rendered-day
input hashes. Without a bump, unchanged evidence can reuse summaries produced
under the previous instructions, or skip model calls entirely.

Changes limited to rendering cached results into Markdown (such as headings,
spacing, or bullet formatting), documentation, or refactoring that preserves
model inputs and output semantics do not require a bump. Distinguish Markdown
rendering from formatting requested of the model; changing the latter requires
a bump.

During review, check prompt and schema edits for the corresponding version bump.
Preserve existing evidence and cached artifacts; the new version invalidates
reuse without deleting them. A bump can cause new model calls on the next run
for every available day with evidence and an existing daily note.
