---
name: bga-readonly
description: Read BGA-connected GitHub, Jira, Confluence, and Elasticsearch data through the organization-managed bga-connections client using a stable read-only approval prefix. Supports provider GET requests, restricted Elastic POST queries, connection discovery, and permissions.
---

# BGA Read-only Wrapper

Use this personal wrapper for read requests through BG AI Gateway. Read the
organization's `~/.codex/skills/bga-connections/SKILL.md` for its access workflow;
this wrapper delegates to that client without changing it or managing credentials.

Invoke the executable directly, expanding `~` to this machine's home directory
when supplying an absolute tool path or approval prefix:

```bash
~/.codex/skills/bga-readonly/scripts/bga-readonly list
~/.codex/skills/bga-readonly/scripts/bga-readonly permissions CONNECTION_UUID
~/.codex/skills/bga-readonly/scripts/bga-readonly get CONNECTION_UUID --path /repos/berkshiregrey/bg_rad_core/pulls/96
```

Discover the current connection UUID with `list` and inspect its `permissions`
before using approved provider endpoints. Reuse discovery and permissions already
obtained in the session; refresh when a connection changes or access fails.
Use repeated `--query key=value` options for pagination or filtering.

For a large response, add `--output /tmp/unique-response.json`, then read the local
file in a separate tool call. The parent directory must exist, and the destination
must not exist (including symlinks). The wrapper creates it with mode 0600 only
after the upstream command succeeds. It does not overwrite files or retry requests.
For `get --output` and `elastic --output`, the wrapper uses the client's download operation and saves
the complete provider body, avoiding the gateway's ordinary call-response size
limit. Without `--output`, it prints the client's response envelope; check its
`status` and `bodyTruncated` fields and use `--output` if the body was truncated.
For `list` and `permissions`, `--output` saves the normal client output.

## Elasticsearch queries

Use `elastic` for the read-only Elasticsearch APIs that require POST. Discover
the matching `elastic:<cluster>` connection and inspect its permissions. Use the
`bg-elasticsearch` skill for site/index selection and time-field guidance.

Write the JSON query to a local file, then invoke the wrapper directly:

```bash
~/.codex/skills/bga-readonly/scripts/bga-readonly elastic CONNECTION_UUID --index rad-bill1-log.records-alias --body-file /tmp/query.json --output /tmp/response.json
```

`--operation` defaults to `search`; the only other choices are `count` and
`field-caps`. These fix the POST endpoint to `/{index}/_search`, `/{index}/_count`,
or `/{index}/_field_caps`. `--index` is required and accepts conventional index
names, `*` wildcards, and comma-separated patterns. It rejects URL/path syntax.
Use either `--body-file` or `--body-text` with one JSON object. Search DSL,
aggregations, sorting, and `search_after` pagination belong in that object.
For example, `field-caps` can use `{"fields":["@timestamp","system_name","message"]}`.

Each Elastic call verifies that the connection is a callable Elastic provider and
that the selected POST endpoint is enabled. It fails closed if this check fails.
The wrapper does not expose general POST, bulk, update/delete-by-query, or
multi-search commands. Unsupported operations use the organization client's
normal authorization workflow; do not bypass the wrapper with a generic POST
when one of these supported read operations suffices.

## Reusable approval

If a sandbox network failure requires escalation, request it with the stable prefix:

```json
["/home/dcolli23/.codex/skills/bga-readonly/scripts/bga-readonly"]
```

Use the current machine's absolute executable path in that prefix. The user can
persist it once for `list`, `permissions`, `get`, and `elastic` across
connection UUIDs, indices, and query bodies. Do not include the UUID or endpoint in the
suggested prefix. Use a direct command without `bash -lc`, redirection, environment
assignments, or shell substitutions; those can prevent normal prefix matching.
Use `--output` instead of `>` and separate local response processing from the
network command. Do not edit Codex approval rules automatically. Managed policy
may still require approval even when a matching user rule exists.

The `get` command fixes the provider method to GET and rejects request bodies.
The `elastic` command fixes POST to the three verified read endpoints above.
Both reject unknown arguments, method overrides, arbitrary headers, full URLs,
and write subcommands. Query values and bodies are passed as data without shell
evaluation. The organization client also uses POST internally to dispatch
requests through the gateway, and gateway endpoint permissions still apply. Only use GET
endpoints with documented read semantics; the method alone does not establish
that an arbitrary endpoint is harmless.

For provider writes or unsupported operations, use the organization skill's
normal authorization workflow. Do not add a general passthrough to this wrapper.
