---
applyTo: "**"
---

# Elasticsearch Query Workflow

## Site and query scope

Resolve RAD log requests from the profiles in
[rad_bg_agents_es_cfg.json](rad_bg_agents_es_cfg.json):

- "FA cell", "ABB FA cell", "Bedford FA cell", `rad_abb_fa`, and its SSH host
  names select the `fa` profile and its fixed system filter.
- BIL, Billerica, RAD Billerica, and bill-autostore select the `bil` profile.
  `bg_arc_N` or "ARC cell N" selects that profile's `bg_arc` system family;
  substitute the requested positive integer cell number into its template.
  For example, "query BIL bg_arc_2" and "query Billerica ARC cell 2" select
  `bg_arc_2`. This family also identifies BIL when the site is omitted.
- For several ARC cells, use an exact `terms` filter with the requested system
  names. For "all BIL ARC cells", use the family's `all_systems_regexp` as a
  `regexp` filter. Do not restrict ARC requests to the legacy `bg_p2_N` default
  values or silently substitute a P2 cell for an ARC cell with no results.
- General BIL requests retain the existing Billerica profile and defaults.
  A numbered BIL cell without a family uses established conversation context;
  clarify the family when both P2 and ARC are plausible.
- Preserve the selected cell for follow-up log questions until the user changes
  it. An explicit alias or system filter overrides the saved route. For other
  sites or datasets, follow the CSV inventory lookup in `SKILL.md`.

Use each profile's `system_scope_field` for exact system filters. BIL's
`system_name` is already a keyword field; FA uses `system_name.keyword`.
Confirm field capabilities if a saved field stops working. An empty result
does not authorize broadening to another cell or index.

The FA profile targets the running Docker cell's verified `bg_p2_fa` log alias,
not the separate prototype `rad-itf` alias. SSH host names are lookup synonyms;
ordinary Elastic searches do not require SSH, a container, or the GAI workspace.

Before the first query, tell the user the site/index, filters, and time range.
An already-requested log investigation authorizes read queries within that scope;
this scope update is not a separate conversational approval gate. Use the time
field appropriate to the dataset as described in `SKILL.md`.
For these profiles, interpret "today" in `America/New_York`, from local midnight
to now, and report times in that timezone unless the user specifies another.

## Preferred transport: BG AI Gateway

Read `~/.codex/skills/bga-readonly/SKILL.md`. Discover connections with `list`,
select the matching `elastic:<cluster>` connection, and inspect its permissions.
Both saved RAD log profiles select `elastic:dev`. Discover its current connection
UUID rather than storing a session-specific UUID in the configuration.

Write the Elasticsearch JSON body to a local file and invoke the wrapper directly:

```bash
~/.codex/skills/bga-readonly/scripts/bga-readonly elastic CONNECTION_UUID --index rad-bill1-log.records-alias --body-file /tmp/query.json --output /tmp/response.json
```

The default operation is `search`; use `--operation count` or
`--operation field-caps` when appropriate. The wrapper verifies the Elastic
provider and endpoint permissions and fixes POST to those read-only endpoints.
Use aggregations for counts/patterns and bounded hits for examples. Check
`timed_out`, shard failures, and `hits.total` versus returned hits; paginate or
narrow the query when necessary. `--output` saves the complete provider response,
but does not itself fetch every Elasticsearch hit.

For sandbox network escalation, use the wrapper's absolute executable path alone
as the reusable approval prefix, as documented in `bga-readonly`. Do not add the
connection UUID, index, operation, or body to the prefix. Avoid shell wrappers,
redirection, and command substitution in the network command. No local Python
environment, Elasticsearch client, or Vault credential retrieval is needed for
this route. Do not install them merely to perform gateway queries.

## Fallback: direct Vault/Elasticsearch access

Use this route only when the gateway connection is unavailable or lacks the
needed access, and report the specific limitation. Gateway permission failures
do not authorize bypassing access controls; direct access must use an independently
authorized credential path. Unsupported operations retain the organization
client's normal authorization requirements.

For Python snippets using direct access, activate the repo-local environment:

```bash
source ~/code/codex-skills/.venvs/bg-elasticsearch/bin/activate
```

For snippets importing `bg_vault_elastic`, prefer the bundled helper:

```bash
BG_ELASTIC_VENV=~/code/codex-skills/.venvs/bg-elasticsearch bash ~/.codex/skills/bg-elasticsearch/scripts/run_bg_vault_elastic_python.sh -c 'from bg_vault_elastic.client import VaultElasticClient; print("import ok")'
```

The helper honors `BG_ELASTIC_VENV`, `BG_ELASTIC_PYTHON`, and
`BG_VAULT_ELASTIC_DIR`; prefer these overrides over machine-specific paths.

Fetch credentials using `VaultElasticClient` and the customer-derived cluster
key, such as `elastic-dev-cluster` for Dev/ITF/Billerica or
`elastic-washington-cluster` for Washington. Use `requests` with basic auth for
direct Elasticsearch calls to avoid client-version incompatibilities. Use the
resolved Elasticsearch endpoint rather than the Kibana URL. Never print
credentials or save them with query results.

## Reporting

Group results by level, message pattern, and relevant timing. Distinguish observed
failures from suspected causes and report missing evidence or incomplete query
results. Identify the connection and exact alias/index actually queried.
