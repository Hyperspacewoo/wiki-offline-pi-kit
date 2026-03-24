#!/usr/bin/env bash
set -euo pipefail

# Canonical runtime + bundle layout for Offgrid Intel Kit.
# - WIKI_KIT_ROOT: immutable code/docs bundle (this repo copy)
# - WIKI_RUNTIME_ROOT: mutable runtime data, venv, maps config, active zims

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_KIT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

export RUN_USER="${RUN_USER:-$(id -un)}"
export RUN_HOME="${RUN_HOME:-$HOME}"
export WIKI_KIT_ROOT="${WIKI_KIT_ROOT:-$DEFAULT_KIT_ROOT}"
export WIKI_RUNTIME_ROOT="${WIKI_RUNTIME_ROOT:-${RUN_HOME}/wiki}"

export WIKI_VENV="${WIKI_VENV:-${WIKI_RUNTIME_ROOT}/.venv}"
export WIKI_DATA_DIR="${WIKI_DATA_DIR:-${WIKI_RUNTIME_ROOT}/data}"
export WIKI_ZIM_DIR="${WIKI_ZIM_DIR:-${WIKI_RUNTIME_ROOT}/zim}"
export WIKI_EBOOK_DIR="${WIKI_EBOOK_DIR:-${WIKI_RUNTIME_ROOT}/ebooks}"
export WIKI_MAPS_DIR="${WIKI_MAPS_DIR:-${WIKI_RUNTIME_ROOT}/maps}"

export ACTIVE_ZIMS_FILE="${ACTIVE_ZIMS_FILE:-${WIKI_DATA_DIR}/active_zims.txt}"
export KIWIX_WRAPPER="${KIWIX_WRAPPER:-${WIKI_KIT_ROOT}/scripts/kiwix-start-from-list.sh}"

ensure_wiki_layout() {
  mkdir -p "${WIKI_DATA_DIR}" "${WIKI_ZIM_DIR}" "${WIKI_EBOOK_DIR}" "${WIKI_MAPS_DIR}/static" "${WIKI_MAPS_DIR}/data"
}

write_layout_env_file() {
  local out="${1:-${WIKI_RUNTIME_ROOT}/layout.env}"
  mkdir -p "$(dirname "$out")"
  cat > "$out" <<EOF
RUN_USER=${RUN_USER}
RUN_HOME=${RUN_HOME}
WIKI_KIT_ROOT=${WIKI_KIT_ROOT}
WIKI_RUNTIME_ROOT=${WIKI_RUNTIME_ROOT}
WIKI_VENV=${WIKI_VENV}
WIKI_DATA_DIR=${WIKI_DATA_DIR}
WIKI_ZIM_DIR=${WIKI_ZIM_DIR}
WIKI_EBOOK_DIR=${WIKI_EBOOK_DIR}
WIKI_MAPS_DIR=${WIKI_MAPS_DIR}
ACTIVE_ZIMS_FILE=${ACTIVE_ZIMS_FILE}
KIWIX_WRAPPER=${KIWIX_WRAPPER}
EOF
}
