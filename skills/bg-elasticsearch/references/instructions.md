---
applyTo: "**"
---

# Elasticsearch Query Workflow

## Site and query scope

Use `~/.codex/skills/bg-elasticsearch/references/rad_bg_agents_es_cfg.json` for
the default RAD Billerica AutoStore logs alias. Billerica, BIL, RAD Billerica,
and bill-autostore refer to this entry. For another site/index, follow the CSV
inventory lookup in `SKILL.md`.

Before the first query, tell the user the site/index, filters, and time range.
An already-requested log investigation authorizes read queries within that scope;
this scope update is not a separate conversational approval gate. Use the time
field appropriate to the dataset as described in `SKILL.md`.

## Preferred transport: BG AI Gateway

Read `~/.codex/skills/bga-readonly/SKILL.md`. Discover connections with `list`,
select the matching `elastic:<cluster>` connection, and inspect its permissions.
For the default Dev/Billerica index, select `elastic:dev`.

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
