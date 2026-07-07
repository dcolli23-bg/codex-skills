#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ENSURE_SCRIPT="${SCRIPT_DIR}/ensure_bill_mongo_forward.sh"
MONGOSH_BIN="${MONGOSH_BIN:-mongosh}"
POD_NAME="${BILL_MONGO_POD:-mongodb-1}"
LOCAL_PORT="${BILL_MONGO_LOCAL_PORT:-27017}"
ALLOW_PRIMARY=0
ALLOW_WRITE=0
EVAL_JS=""

usage() {
  cat >&2 <<USAGE
Usage: bill_mongo_eval.sh [--pod mongodb-0|mongodb-1|mongodb-2] [--port PORT] [--allow-primary] [--allow-write] [--eval JS | JS]

Runs a guarded mongosh --eval against the Billerica MongoDB port-forward.
Use '-' as JS to read the eval body from stdin.
USAGE
}

log() {
  printf '%s\n' "$*" >&2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pod)
      POD_NAME="${2:-}"
      shift 2
      ;;
    --port)
      LOCAL_PORT="${2:-}"
      shift 2
      ;;
    --allow-primary)
      ALLOW_PRIMARY=1
      shift
      ;;
    --allow-write)
      ALLOW_WRITE=1
      shift
      ;;
    --eval)
      EVAL_JS="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      if [[ -z "$EVAL_JS" ]]; then
        EVAL_JS="$1"
        shift
      else
        usage
        exit 2
      fi
      ;;
  esac
done

if [[ "$EVAL_JS" == "-" ]]; then
  EVAL_JS="$(cat)"
fi

if [[ -z "$EVAL_JS" ]]; then
  usage
  exit 2
fi

if ! command -v "$MONGOSH_BIN" >/dev/null 2>&1; then
  log "mongosh not found. Set MONGOSH_BIN if it is installed under a different name."
  exit 127
fi

if ! [[ "$POD_NAME" =~ ^mongodb-[0-2]$ ]]; then
  log "Invalid pod: ${POD_NAME}"
  usage
  exit 2
fi

if ! [[ "$LOCAL_PORT" =~ ^[0-9]+$ ]] || (( LOCAL_PORT < 1 || LOCAL_PORT > 65535 )); then
  log "Invalid local port: ${LOCAL_PORT}"
  usage
  exit 2
fi

guard_read_only() {
  local js="$1"
  local forbidden

  forbidden='(^|[^[:alnum:]_$])(insert|insertOne|insertMany|update|updateOne|updateMany|replaceOne|deleteOne|deleteMany|remove|drop|dropDatabase|dropCollection|createCollection|createIndex|createIndexes|dropIndex|dropIndexes|renameCollection|bulkWrite|findOneAndUpdate|findOneAndReplace|findOneAndDelete|save|initializeUnorderedBulkOp|initializeOrderedBulkOp|reIndex|compact|repairDatabase|shutdownServer|fsyncLock|adminCommand|runCommand)[[:space:]]*\('

  if [[ "$js" =~ $forbidden || "$js" =~ rs\.(stepDown|reconfig|initiate|add|remove)[[:space:]]*\( ]]; then
    log "Refusing to run JavaScript that looks like a write/admin operation."
    log "Use --allow-write only after explicit confirmation."
    return 1
  fi
}

if (( ALLOW_WRITE == 0 )); then
  guard_read_only "$EVAL_JS"
fi

URI="$("$ENSURE_SCRIPT" --pod "$POD_NAME" --port "$LOCAL_PORT")"

IS_PRIMARY="$("$MONGOSH_BIN" "$URI" --quiet --eval 'db.hello().isWritablePrimary ? "true" : "false"')"

if [[ "$IS_PRIMARY" == "true" && "$ALLOW_PRIMARY" -eq 0 ]]; then
  log "Refusing to run because the forwarded pod is currently primary."
  log "Use --pod mongodb-1 or --pod mongodb-2 for a secondary, or --allow-primary after explicit confirmation."
  exit 1
fi

"$MONGOSH_BIN" "$URI" --quiet --eval "$EVAL_JS"
