---
name: bga-readonly
description: Read BGA-connected provider data through the organization-managed bga-connections client using a stable, GET-only approval prefix. Use for BG GitHub PR descriptions, reviews, comments, files, and other approved GET endpoints, including connection discovery and permissions.
---

# BGA Read-only Wrapper

Use this personal wrapper for read requests through BG AI Gateway. Read the
organization's `~/.codex/skills/bga-connections/SKILL.md` for its access workflow;
this wrapper delegates to that client without changing it or managing credentials.

Invoke the executable directly using this exact absolute path:

```bash
/home/dcolli23/.codex/skills/bga-readonly/scripts/bga-readonly list
/home/dcolli23/.codex/skills/bga-readonly/scripts/bga-readonly permissions CONNECTION_UUID
/home/dcolli23/.codex/skills/bga-readonly/scripts/bga-readonly get CONNECTION_UUID --path /repos/berkshiregrey/bg_rad_core/pulls/96
```

Discover the current connection UUID with `list` and inspect its `permissions`
before using approved provider endpoints. Reuse discovery and permissions already
obtained in the session; refresh when a connection changes or access fails.
Use repeated `--query key=value` options for pagination or filtering.

For a large response, add `--output /tmp/unique-response.json`, then read the local
file in a separate tool call. The parent directory must exist, and the destination
must not exist (including symlinks). The wrapper creates it with mode 0600 only
after the upstream command succeeds. It does not overwrite files or retry requests.
For `get --output`, the wrapper uses the client's GET download operation and saves
the complete provider body, avoiding the gateway's ordinary call-response size
limit. Without `--output`, it prints the client's response envelope; check its
`status` and `bodyTruncated` fields and use `--output` if the body was truncated.
For `list` and `permissions`, `--output` saves the normal client output.

## Reusable approval

If a sandbox network failure requires escalation, request it with the stable prefix:

```json
["/home/dcolli23/.codex/skills/bga-readonly/scripts/bga-readonly"]
```

The user can persist this approval once for `list`, `permissions`, and `get` across
connection UUIDs and endpoint paths. Do not include the UUID or endpoint in the
suggested prefix. Use a direct command without `bash -lc`, redirection, environment
assignments, or shell substitutions; those can prevent normal prefix matching.
Use `--output` instead of `>` and separate local response processing from the
network command. Do not edit Codex approval rules automatically. Managed policy
may still require approval even when a matching user rule exists.

The wrapper fixes the provider method to GET and rejects unknown arguments,
method overrides, request bodies, arbitrary headers, full URLs, and write
subcommands. Query values are passed as data without shell evaluation. The
organization client still uses POST internally to dispatch the provider GET
through the gateway, and gateway endpoint permissions still apply. Only use GET
endpoints with documented read semantics; the method alone does not establish
that an arbitrary endpoint is harmless.

For provider writes or unsupported operations, use the organization skill's
normal authorization workflow. Do not add a general passthrough to this wrapper.
