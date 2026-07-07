---
name: billerica-mongo
description: Use when the user asks to query, inspect, summarize, or analyze the Billerica/BIL/bill1 MongoDB instance, including requests mentioning "billerica mongo", "bill mongo", "bil mongo", "mongodb-7", `pick_stats` SKU/product counts, or plain-language requests like "query the billerica mongo instance for ...".
---

# Billerica MongoDB

Use this skill for read-only MongoDB inspection against the Billerica `mongodb-7` Kubernetes namespace.

## Connection

Use the bundled scripts rather than hand-writing port-forward logic:

```bash
~/.codex/skills/billerica-mongo/scripts/bill_mongo_eval.sh --eval '<javascript>'
```

The eval script calls `ensure_bill_mongo_forward.sh`, which starts or reuses:

```text
kubectl --context k8s/bg-rad-bill1-context -n mongodb-7 port-forward pod/mongodb-1 27017:27017
```

If the default context cannot read the namespace, it falls back to:

```text
k8s/bg-rad-bill1-context-(privileged)
```

The default URI is:

```text
mongodb://127.0.0.1:27017/?directConnection=true&readPreference=secondary
```

## Safety Rules

- Treat the instance as production-like. MongoDB authorization is disabled, so client-side guardrails matter.
- Default to `mongodb-1`, which is expected to be a secondary.
- Do not run write, DDL, index, replica-set, or admin commands unless the user explicitly asks and confirms.
- The eval helper refuses obvious write/admin JavaScript unless `--allow-write` is passed.
- The eval helper refuses to run if the forwarded pod is primary unless `--allow-primary` is passed.
- For normal plain-language queries, use read-only commands: `find`, `findOne`, `countDocuments`, `distinct`, `aggregate` with read-only stages, `getCollectionNames`, and small samples with `limit`.

## Workflow

1. Translate the user's plain-language request into a small read-only `mongosh` JavaScript snippet.
2. If the database or collection is unknown, first inspect with read-only commands:

```bash
~/.codex/skills/billerica-mongo/scripts/bill_mongo_eval.sh --eval 'db.getMongo().getDBNames()'
~/.codex/skills/billerica-mongo/scripts/bill_mongo_eval.sh --eval 'db.getSiblingDB("DATABASE").getCollectionNames()'
~/.codex/skills/billerica-mongo/scripts/bill_mongo_eval.sh --eval 'db.getSiblingDB("DATABASE").COLLECTION.findOne()'
```

3. Keep result sets bounded with `limit`, `$limit`, projections, or counts.
4. In the final answer, include the actual query or aggregation that was run and summarize the result.

## Known Query Shortcuts

### `pick_stats` SKU Counts

For requests like "count docs in `pick_stats` for SKU X" against Billerica log DBs such as `bg_p2_3_log` and `bg_p2_4_log`, query the `pick_stats` product fields directly before inspecting product databases or joining through `graspable`, `perception_view`, or `picks`.

`pick_stats` stores SKU/product identifiers as BSON binary values in top-level fields:

- `product`
- `expected_product`

Encode the SKU string as UTF-8 base64 and query those fields with `BinData(0, ...)`:

```bash
~/.codex/skills/billerica-mongo/scripts/bill_mongo_eval.sh --eval '
const sku = "USB-A-TO-MICRO-1";
const skuBin = BinData(0, Buffer.from(sku, "utf8").toString("base64"));
const dbs = ["bg_p2_3_log", "bg_p2_4_log"];
const out = {};
let total = 0;
for (const dbName of dbs) {
  const count = db.getSiblingDB(dbName).pick_stats.countDocuments({
    $or: [{ product: skuBin }, { expected_product: skuBin }]
  });
  out[dbName] = count;
  total += count;
}
out.total = total;
printjson(out);
'
```

Only inspect product databases or related log collections if the direct `product` / `expected_product` query returns zero, the user asks for product metadata, or the task needs relationship details beyond the count.

## Performance Notes

- Avoid running multiple `bill_mongo_eval.sh` commands in parallel. The helper manages one local port-forward state file, so parallel runs can churn or invalidate the tunnel.
- Keep exploratory samples projected and bounded. `pick_stats` documents can contain large trajectory payloads, so exclude fields such as `trajectory_pick`, `trajectory_place`, and `trajectory_putback` when serializing documents for inspection.

## Port-Forward Utilities

Check status:

```bash
~/.codex/skills/billerica-mongo/scripts/ensure_bill_mongo_forward.sh --status
```

Stop the managed port-forward:

```bash
~/.codex/skills/billerica-mongo/scripts/ensure_bill_mongo_forward.sh --stop
```

Forward a specific pod only when needed:

```bash
~/.codex/skills/billerica-mongo/scripts/bill_mongo_eval.sh --pod mongodb-2 --eval 'db.hello()'
```
