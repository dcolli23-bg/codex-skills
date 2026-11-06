# Box copy, revision, and render workflow

Use BG AI Gateway for the user-approved binary upload and rendering workflow.
Read `~/.codex/skills/bga-connections/SKILL.md` and
`~/.codex/skills/bga-readonly/SKILL.md` for current access and approval rules.
The Box skill's content-workflows reference supplies additional Box guidance;
do not substitute a text-only upload tool for binary PPTX content.

## Saved assets

These IDs were verified on November 5, 2026. Revalidate them; they are discovery
hints, not proof of current permissions or fixed template versions.

| Asset | ID / location |
| --- | --- |
| Reusable BG retro template | File `2572784987648`, `sprint-retro-template.pptx` |
| Personal presentation folder | Folder `434751995676`, `All Files / dylan.colli / sprint-retro-presentations` |
| Expected actor | Dylan Colli; previously user `35745323966` |

Use the template's **current** version, not a frozen historical version. If an
asset moved, inspect its metadata or search by exact name and verify its parent.
If missing or ambiguous, ask rather than creating a replacement template or
silently uploading to the Box root.

## Discover and read

Use the installed read wrapper directly, with `--output` for full responses:

```bash
~/.codex/skills/bga-readonly/scripts/bga-readonly list
~/.codex/skills/bga-readonly/scripts/bga-readonly permissions CONNECTION_UUID
~/.codex/skills/bga-readonly/scripts/bga-readonly get CONNECTION_UUID \
  --path /users/me
~/.codex/skills/bga-readonly/scripts/bga-readonly get CONNECTION_UUID \
  --path /files/2572784987648 \
  --query fields=id,name,parent,etag,sha1,file_version,permissions,lock \
  --output /absolute/work/source/template-metadata.json
```

Also read destination metadata/permissions and paginate its items before choosing
a collision-free name. Use `Sprint N Retrospective.pptx` when unused; otherwise
add a local timestamp and, if necessary, a numeric suffix. Do not trust the
filename alone when an explicit update request identifies a deck.

Download the template bytes from `/files/2572784987648/content`. Save its metadata,
file-version ID, and hashes. The read wrapper can download binary content with
`--output`. Use unique output paths because it refuses overwrites.

## Create a working copy

Use an approved copy endpoint if available. If it is not enabled, download the
template and upload **identical bytes** under the new sprint filename as the
copy-equivalent. Do not request additional endpoints just to avoid that proven
alternative. Record the new working file ID and download/verify its bytes before
authoring. Leave any lock on the template alone.

Discover the organization client's current CLI help and advertised endpoints
before using these command shapes. `CONNECTION_UUID` is discovered per session,
not a stored constant. The current client is:

```text
~/.codex/skills/bga-connections/bga-connections.py
```

New binary file (multipart attributes must precede the file):

```bash
python3 ~/.codex/skills/bga-connections/bga-connections.py call CONNECTION_UUID \
  --method POST --url https://upload.box.com/api/2.0/files/content \
  --multipart-text 'attributes={"name":"Sprint N Retrospective.pptx","parent":{"id":"434751995676"}}' \
  --multipart-file file=/absolute/work/source/template.pptx
```

An explicit update uses the existing file as the local starting point instead
of copying the template again. Verify it belongs in the intended personal folder,
is not the reusable template, and permits content updates.

## Upload authored revisions

The binary **Update file contents** route is:

```bash
python3 ~/.codex/skills/bga-connections/bga-connections.py call CONNECTION_UUID \
  --method POST --url https://upload.box.com/api/2.0/files/WORKING_FILE_ID/content \
  --header 'If-Match: OBSERVED_ETAG' \
  --multipart-text 'attributes={"name":"Sprint N Retrospective.pptx"}' \
  --multipart-file file=/absolute/work/output/retro-r1.pptx
```

Use the working file's actual name, including any collision suffix.
`PUT /files/{id}` edits metadata only. Never upload revisions to the template ID.
Immediately before each write, verify the observed etag/version still matches
the last known working state; send `If-Match` where supported. Stop on conflict,
lock, or precondition failure. Do not widen approvals or bypass an unavailable
endpoint. Save the response and read the file with the same actor to verify
`sha1` and `file_version.id` against the uploaded bytes.

If a write times out, inspect current metadata: a matching SHA1 may mean the
write succeeded. Do not blindly create a duplicate or append another revision.

## Render the exact version

The read wrapper does not accept headers or full URLs. Use the organization
client for the representation hint and observed Box Cloud asset URL:

```bash
python3 ~/.codex/skills/bga-connections/bga-connections.py download CONNECTION_UUID \
  --method GET --path /files/WORKING_FILE_ID \
  --query fields=id,name,etag,sha1,file_version,representations \
  --header 'X-Rep-Hints: [pdf]' \
  --output /absolute/work/QA/representation-r1-check1.json
```

Headers use **`Name: value`**, not `Name=value`. Inspect the downloaded provider
body, not just a truncated call envelope. Confirm:

- `file_version.id` equals the upload's verified version.
- The chosen entry is the PDF representation and `status.state` is `success`.
- Its observed `info.url` / content URL identifies that same version. If the
  response cannot establish version identity, do not accept the render.

For `pending`/`none`, follow the returned representation `info.url` when provided
to request/poll generation, and refresh metadata as needed within the entrypoint's
polling bound. A request for a render may be necessary before pending becomes
success. On `error`, inspect the structural report and package serialization
before changing anything; repeated identical uploads are not a fix.

For a successful PDF, take `content.url_template` from the response. Remove only
the literal `{+asset_path}` placeholder, retaining the trailing `/content/`:

```bash
python3 ~/.codex/skills/bga-connections/bga-connections.py download CONNECTION_UUID \
  --method GET --url OBSERVED_BOX_CLOUD_CONTENT_URL \
  --output /absolute/work/QA/box-VERSION/retro.pdf
pdfinfo /absolute/work/QA/box-VERSION/retro.pdf
pdftoppm -png -r 120 /absolute/work/QA/box-VERSION/retro.pdf \
  /absolute/work/QA/box-VERSION/slide
```

Create the local QA directory first. Use only observed, permitted asset URLs
through the gateway; do not guess signed URLs or expose credentials. Inspect all
PNG files with the image-viewing tool. Store each version's PDF/images separately
so an older successful render cannot be mistaken for the latest revision.

Recheck file metadata after QA. If its version changed during rendering, stop
and reconcile rather than claiming the current deck passed. Deliver
`https://app.box.com/file/WORKING_FILE_ID`; this is an authenticated file URL,
not a newly created shared link.
