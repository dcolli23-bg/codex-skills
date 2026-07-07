#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: bash scripts/run_bg_vault_elastic_python.sh <python args>" >&2
  exit 2
fi

BG_VAULT_ELASTIC_DIR="${BG_VAULT_ELASTIC_DIR:-$HOME/bg-vault-client/bg_vault_elastic}"
BG_ELASTIC_VENV="${BG_ELASTIC_VENV:-}"
BG_ELASTIC_PYTHON="${BG_ELASTIC_PYTHON:-}"

if [[ ! -d "${BG_VAULT_ELASTIC_DIR}" ]]; then
  echo "bg_vault_elastic checkout not found at ${BG_VAULT_ELASTIC_DIR}" >&2
  echo "Set BG_VAULT_ELASTIC_DIR to your bg_vault_elastic checkout directory." >&2
  exit 1
fi

if [[ -z "${BG_ELASTIC_PYTHON}" && -n "${BG_ELASTIC_VENV}" ]]; then
  BG_ELASTIC_PYTHON="${BG_ELASTIC_VENV}/bin/python"
fi

if [[ -n "${BG_ELASTIC_PYTHON}" ]]; then
  if [[ ! -x "${BG_ELASTIC_PYTHON}" ]]; then
    echo "Python executable not found at ${BG_ELASTIC_PYTHON}" >&2
    echo "Set BG_ELASTIC_PYTHON or BG_ELASTIC_VENV to a usable Python environment." >&2
    exit 1
  fi
  export PYTHONPATH="${BG_VAULT_ELASTIC_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}"
  cd "${BG_VAULT_ELASTIC_DIR}"
  exec "${BG_ELASTIC_PYTHON}" "$@"
fi

if [[ -n "${UV_BIN:-}" ]]; then
  uv_bin="${UV_BIN}"
elif [[ -x "$HOME/.local/bin/uv" ]]; then
  uv_bin="$HOME/.local/bin/uv"
elif command -v uv >/dev/null 2>&1; then
  uv_bin="$(command -v uv)"
else
  echo "uv was not found. Install uv or set UV_BIN to its full path." >&2
  exit 1
fi

cd "${BG_VAULT_ELASTIC_DIR}"
exec "${uv_bin}" run python "$@"
