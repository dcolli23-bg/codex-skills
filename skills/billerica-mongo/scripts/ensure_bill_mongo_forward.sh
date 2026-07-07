#!/usr/bin/env bash
set -euo pipefail

KUBECTL_BIN="${KUBECTL_BIN:-kubectl}"
NAMESPACE="${BILL_MONGO_NAMESPACE:-mongodb-7}"
DEFAULT_CONTEXT="${BILL_MONGO_CONTEXT:-k8s/bg-rad-bill1-context}"
PRIVILEGED_CONTEXT="${BILL_MONGO_PRIVILEGED_CONTEXT:-${DEFAULT_CONTEXT}-(privileged)}"
POD_NAME="${BILL_MONGO_POD:-mongodb-1}"
LOCAL_PORT="${BILL_MONGO_LOCAL_PORT:-27017}"
TMP_BASE="${TMPDIR:-/tmp}"
STATE_PREFIX="${TMP_BASE}/bill-mongo-${USER:-user}-${LOCAL_PORT}"
PID_FILE="${BILL_MONGO_PID_FILE:-${STATE_PREFIX}.pid}"
META_FILE="${BILL_MONGO_META_FILE:-${STATE_PREFIX}.env}"
LOG_FILE="${BILL_MONGO_LOG_FILE:-${STATE_PREFIX}.log}"
MODE="ensure"

usage() {
  cat >&2 <<USAGE
Usage: ensure_bill_mongo_forward.sh [--pod mongodb-0|mongodb-1|mongodb-2] [--port PORT] [--status] [--stop]

Starts or reuses localhost:PORT -> mongodb-7/POD:27017.
Prints the MongoDB URI on stdout when the tunnel is available.
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
      STATE_PREFIX="${TMP_BASE}/bill-mongo-${USER:-user}-${LOCAL_PORT}"
      PID_FILE="${BILL_MONGO_PID_FILE:-${STATE_PREFIX}.pid}"
      META_FILE="${BILL_MONGO_META_FILE:-${STATE_PREFIX}.env}"
      LOG_FILE="${BILL_MONGO_LOG_FILE:-${STATE_PREFIX}.log}"
      shift 2
      ;;
    --status)
      MODE="status"
      shift
      ;;
    --stop)
      MODE="stop"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage
      exit 2
      ;;
  esac
done

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

mongo_uri() {
  printf 'mongodb://127.0.0.1:%s/?directConnection=true&readPreference=secondary\n' "$LOCAL_PORT"
}

pid_alive() {
  local pid="$1"
  [[ -n "$pid" ]] && kill -0 "$pid" >/dev/null 2>&1
}

managed_process() {
  local pid="$1"
  local cmdline

  [[ -r "/proc/${pid}/cmdline" ]] || return 0
  cmdline="$(tr '\0' ' ' <"/proc/${pid}/cmdline")"
  [[ "$cmdline" == *"kubectl"* && "$cmdline" == *"port-forward"* && "$cmdline" == *"pod/${POD_NAME}"* && "$cmdline" == *"${LOCAL_PORT}:27017"* ]]
}

read_pid() {
  [[ -f "$PID_FILE" ]] && sed -n '1p' "$PID_FILE"
}

port_open() {
  timeout 1 bash -c "</dev/tcp/127.0.0.1/${LOCAL_PORT}" >/dev/null 2>&1
}

wait_for_port() {
  local deadline=$((SECONDS + 15))

  while (( SECONDS < deadline )); do
    if port_open; then
      return 0
    fi
    sleep 0.25
  done

  return 1
}

clean_state() {
  rm -f "$PID_FILE" "$META_FILE"
}

select_context() {
  if "$KUBECTL_BIN" --context "$DEFAULT_CONTEXT" get namespace "$NAMESPACE" --request-timeout=5s >/dev/null 2>&1; then
    printf '%s\n' "$DEFAULT_CONTEXT"
  else
    printf '%s\n' "$PRIVILEGED_CONTEXT"
  fi
}

status() {
  local pid
  pid="$(read_pid || true)"

  if pid_alive "$pid" && managed_process "$pid"; then
    if port_open; then
      log "bill mongo port-forward is running: pid=${pid}, pod=${POD_NAME}, local_port=${LOCAL_PORT}"
      mongo_uri
      return 0
    fi
    log "bill mongo port-forward pid exists but localhost:${LOCAL_PORT} is not responding: pid=${pid}"
    return 1
  fi

  if [[ -n "$pid" ]]; then
    log "stale bill mongo port-forward pid: ${pid}"
  else
    log "bill mongo port-forward is not running"
  fi
  return 1
}

stop_forward() {
  local pid
  pid="$(read_pid || true)"

  if pid_alive "$pid" && managed_process "$pid"; then
    kill "$pid"
    log "stopped bill mongo port-forward: pid=${pid}"
  else
    log "no managed bill mongo port-forward to stop"
  fi

  clean_state
}

ensure_forward() {
  local pid context
  pid="$(read_pid || true)"

  if pid_alive "$pid" && managed_process "$pid"; then
    if port_open || wait_for_port; then
      log "reusing bill mongo port-forward: pid=${pid}, pod=${POD_NAME}, local_port=${LOCAL_PORT}"
      mongo_uri
      return 0
    fi

    log "managed port-forward is not responding; stopping pid=${pid}"
    kill "$pid" >/dev/null 2>&1 || true
    clean_state
  elif [[ -n "$pid" ]]; then
    log "removing stale bill mongo port-forward pid: ${pid}"
    clean_state
  fi

  if port_open; then
    log "localhost:${LOCAL_PORT} is already in use, but not by the managed bill mongo port-forward"
    log "set BILL_MONGO_LOCAL_PORT or pass --port to use a different local port"
    return 1
  fi

  context="$(select_context)"
  log "starting bill mongo port-forward: context=${context}, namespace=${NAMESPACE}, pod=${POD_NAME}, local_port=${LOCAL_PORT}"

  nohup "$KUBECTL_BIN" --context "$context" -n "$NAMESPACE" port-forward "pod/${POD_NAME}" "${LOCAL_PORT}:27017" >"$LOG_FILE" 2>&1 &
  pid="$!"

  printf '%s\n' "$pid" >"$PID_FILE"
  {
    printf 'context=%q\n' "$context"
    printf 'namespace=%q\n' "$NAMESPACE"
    printf 'pod=%q\n' "$POD_NAME"
    printf 'local_port=%q\n' "$LOCAL_PORT"
    printf 'log_file=%q\n' "$LOG_FILE"
  } >"$META_FILE"

  if wait_for_port; then
    log "bill mongo port-forward is ready: pid=${pid}, log=${LOG_FILE}"
    mongo_uri
    return 0
  fi

  log "port-forward did not become ready; log follows:"
  tail -n 40 "$LOG_FILE" >&2 || true
  kill "$pid" >/dev/null 2>&1 || true
  clean_state
  return 1
}

case "$MODE" in
  ensure)
    ensure_forward
    ;;
  status)
    status
    ;;
  stop)
    stop_forward
    ;;
esac
