---
applyTo: "**"
---

# Elasticsearch Query Workflow

When the user asks to query Elasticsearch logs (e.g. "query ES for...", "check logs in...", "summarize activity for..."), follow this workflow.

## Setup

**Venv:** Always activate before running any Python. Use the repo-local
environment from the codex-skills checkout:
```bash
source ~/code/codex-skills/.venvs/bg-elasticsearch/bin/activate && python3 - << 'EOF'
...
EOF
```

If the snippet needs `bg_vault_elastic`, prefer the bundled helper:
```bash
BG_ELASTIC_VENV=~/code/codex-skills/.venvs/bg-elasticsearch bash scripts/run_bg_vault_elastic_python.sh -c 'from bg_vault_elastic.client import VaultElasticClient; print("import ok")'
```

The helper uses:
- `BG_ELASTIC_VENV` when it is set
- `BG_ELASTIC_PYTHON` when it is set
- `BG_VAULT_ELASTIC_DIR` when it is set

If those are not set, the helper falls back to its local defaults. Prefer environment overrides instead of hardcoding host-specific paths into query snippets.

**Config file:** `~/.codex/skills/bg-elasticsearch/references/rad_bg_agents_es_cfg.json`
- Contains the default RAD Billerica AutoStore entry with `elastic_url`, `index_alias`, `customer`, `site`, and optional system scoping
- Use this entry by default when the user does not specify another Elasticsearch site/index
- Treat Billerica, BIL, Billerica AutoStore, RAD Billerica, and bill-autostore as this default entry

**Credentials:** Use `VaultElasticClient` with the cluster key derived from the customer name:
- Washington -> `"elastic-washington-cluster"`
- Dev/ITF -> `"elastic-dev-cluster"`
- Huron -> `"elastic-huron-cluster"`
- Sunflower -> `"elastic-sunflower-cluster"`
- Britton -> `"elastic-britton-cluster"`
- Maunakea -> `"elastic-maunakea-cluster"`

**ES Client:** Use `elasticsearch` v8 (`pip show elasticsearch` should show 8.x). Use `basic_auth` (not `http_auth`):

```python
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from bg_vault_elastic.client import VaultElasticClient
from elasticsearch import Elasticsearch

with Path("~/.codex/skills/bg-elasticsearch/references/rad_bg_agents_es_cfg.json").expanduser().open() as f:
    configs = json.load(f)

cfg = configs[0]

client = VaultElasticClient()
creds = client.get_es_credentials("elastic-dev-cluster")

es = Elasticsearch(hosts=cfg["elastic_url"], basic_auth=(creds["username"], creds["password"]))

now = datetime.now(timezone.utc)
since = now - timedelta(minutes=15)

query = {
    "query": {
        "bool": {
            "must": [
                {"match": {"field": "value"}},
                {"range": {"@timestamp": {"gte": since.isoformat(), "lte": now.isoformat()}}}
            ]
        }
    },
    "size": 500,
    "sort": [{"@timestamp": {"order": "asc"}}]
}

result = es.search(index=cfg["index_alias"], body=query)
hits = result["hits"]["hits"]
print(f"Total hits: {result['hits']['total']['value']}")
for hit in hits:
    src = hit["_source"]
    print(f"{src.get('@timestamp')} | {src.get('level', '')} | {src.get('message', '')}")
```

## Workflow

1. **Confirm before running** -- show the user the site/index, query filters, and time range before executing
2. **Select config entry** by `site` or `customer` from the config file
3. **Use `requests`** (not the `Elasticsearch` client) due to version incompatibility
4. **Summarize results** -- after fetching hits, group by log level or message pattern and give a human-readable summary
