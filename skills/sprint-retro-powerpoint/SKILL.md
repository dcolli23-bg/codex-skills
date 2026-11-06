---
name: sprint-retro-powerpoint
description: Generate an editable BG PowerPoint from an existing sprint folder in Dylan's journal, upload it to Box, and visually verify Box-rendered slides. Use for deck generation or an explicit deck update, not retrospective research or Markdown-only outlines.
---

# Sprint Retro PowerPoint

Turn a folder under `~/journal/sprint-retros/` into a short, template-based
PowerPoint in Dylan's personal Box space. Use the existing research; do not
launch another GitHub, Jira, Confluence, or Slack sweep.

Example: `Use $sprint-retro-powerpoint for sprint-24.`
An absolute path to that sprint folder is also accepted.

## Read the selected sprint

Read applicable home/vault instructions. Resolve the input beneath
`~/journal/sprint-retros/`, including symlinks; reject paths outside that root.
Never silently choose the latest sprint. If the folder is unspecified, ask which
one to use.

Read the latest overview and slide outline in the folder. The established names
are `Sprint N.md` and `Slide outline.md`; inspect rather than assuming every
folder uses those names. If either is missing or ambiguous, ask for the intended
source. Offer `$sprint-retro` for missing research or outlines, but do not run it
as an unrequested prerequisite.

Use the outline's structure and the overview's current facts/status. Reconcile
straightforward differences, such as a formerly pending merge, without editing
the notes. Ask about substantive conflicts or changes in emphasis. Preserve the
source's reporting window and metric definitions; do not advance the cutoff,
invent dates, or equate diff volume with lines proven read. Distinguish merged,
deployed, tested, and accepted. Keep proposals distinct from commitments.

Create a unique local workspace with source snapshots, output revisions, and QA
artifacts. Record source paths and SHA256 hashes. **Source notes and the reusable
Box template are read-only.** Before final acceptance, reread/hash the originals;
if they changed, reconcile the deck against the new content or report the need
to refresh. Never restore a snapshot over the user's edits.

## Prepare the Box working file

Read [the Box workflow](references/box-workflow.md) for saved asset IDs, gateway
commands, and exact-version rendering. Discover the current connection and
permissions; verify the actor, template, and destination before writing.

- **New invocation:** create a new sprint-specific working copy. If a same-sprint
  deck exists, use a distinct filename rather than updating it implicitly.
- **Explicit update request:** resolve the intended existing file, download and
  inspect its latest version, and preserve unrelated user edits. Ask if the
  target or scope is ambiguous. Never rebuild over it blindly.
- **Revisions within one invocation:** keep the same Box file ID throughout the
  upload → render → inspect → fix loop. Do not make a new copy for each revision.

Use the saved template and personal presentation folder unless Dylan specifies
others. Do not create sharing links, change collaborations, unlock an Office
file, or modify the source template. Honor tool/network approvals at execution;
permission to read does not grant permission to write.

## Author locally

Use Python's standard-library `zipfile` and XML tools to modify the downloaded
PPTX. This is the user-approved alternative to the unavailable artifact
presentation runtime. Do not require PowerPoint, `@oai/artifact-tool`,
`load_workspace_dependencies`, or `python-pptx`.

Follow [template-preserving authoring](references/authoring.md). Inspect the
actual template before choosing slide shapes/layouts. Retain editable text,
speaker notes, native fonts, geometry, masters, layouts, themes, and artwork.
Do not flatten slides into images or resave the deliverable through LibreOffice.

Match the requested outline and slide count, usually two or three slides. Keep
on-slide copy concise. Put definitions, reporting cutoffs, caveats, and evidence
pointers in speaker notes. Preserve the balance between owned delivery and
review workload established by the notes.

For substantial authoring, an available worker can own the local PPTX/build
script while the coordinator owns source reconciliation and final visual QA.
Give workers snapshots and a disjoint output directory, not write access to
notes or the template. If delegation is unavailable, work directly and disclose
that independent review was unavailable.

## Upload, render, inspect

1. Run the package validator against the template (or latest deck for an explicit
   update), with the intended slide count and speaker notes required:

   ```bash
   python3 ~/.codex/skills/sprint-retro-powerpoint/scripts/validate_pptx.py \
     /absolute/work/output/retro-r1.pptx \
     --template /absolute/work/source/template.pptx \
     --expected-slides 3 --require-notes
   ```

   Save the JSON report. This is structural validation, **not visual acceptance**.
2. Recheck the working file's version/etag before each upload. Stop on an
   intervening edit; do not overwrite or retry a failed precondition blindly.
   Upload with the gateway's **Update file contents** endpoint. Metadata updates
   do not replace PPTX bytes. Confirm the resulting version and SHA1 with a
   same-actor read.
3. Request a Box PDF representation of that exact uploaded `file_version`.
   Poll at most ten times over at most five minutes, respecting `Retry-After`.
   Reject stale versions. Stop on rendering errors or exhausted polling and
   retain the last verified artifact; do not claim successful QA.
4. Convert the PDF to PNGs with `pdftoppm` and inspect **every slide**, not just
   extracted text. Check clipping, overlap, awkward wraps, hierarchy, contrast,
   legibility, and template fidelity. Also check slide count, narrative,
   speaker notes, metrics, and statuses against the source snapshots.
5. Fix locally and upload another revision to the **same file**. Allow an initial
   authored upload plus up to three corrective uploads. Stop earlier if correct;
   if still failing, report the remaining issue and ask before further writes.

Do not upload identical bytes repeatedly to stimulate rendering. After a timeout
with an uncertain write result, read the current version/hash before retrying.
If cancelled, stop this run's workers and requests without deleting remote files
or reverting user edits.

## Acceptance and handoff

Confirm that the final remote version/hash matches the local PPTX and the
version represented by the inspected images. Check source notes and template
were not modified by this run. For delegated authoring, the coordinator inspects
the final images independently of the author.

Return the authenticated Box file URL, sprint source folder, and concise QA
status. Keep the local PPTX, PDF/PNGs, build script, and a manifest with source
hashes, file/version IDs, uploaded hashes, and validation results for follow-up.
State material limitations: **Box rendering was verified, not desktop Microsoft
PowerPoint rendering.** If only an offline draft was possible, label it unverified.
