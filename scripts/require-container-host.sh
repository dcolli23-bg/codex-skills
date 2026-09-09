#!/usr/bin/env bash

set -euo pipefail

readonly REQUIRED_HOSTNAME="dylan-lambda"
current_hostname="$(hostname)"

if [[ "${current_hostname}" != "${REQUIRED_HOSTNAME}" ]]; then
  printf >&2 '%s\n' \
    "Container skill host check failed." \
    "Current hostname: ${current_hostname}" \
    "Required hostname: ${REQUIRED_HOSTNAME}" \
    "GAI, UMI/SUMI, RAD P2, and other container skills cannot be run on this host."
  exit 1
fi
