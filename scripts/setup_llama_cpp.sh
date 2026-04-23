#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/layout.sh"

if ! command -v cmake >/dev/null 2>&1 || ! command -v make >/dev/null 2>&1 || ! command -v g++ >/dev/null 2>&1; then
  echo "Installing llama.cpp build deps..."
  "${WIKI_KIT_ROOT}/scripts/install_prereqs_portable.sh"
fi

if [[ ! -f "${LLAMA_CPP_ROOT}/CMakeLists.txt" ]]; then
  echo "Ensuring llama.cpp source is present..."
  "${WIKI_KIT_ROOT}/scripts/install_prereqs_portable.sh"
fi

if [[ ! -f "${LLAMA_CPP_ROOT}/CMakeLists.txt" ]]; then
  echo "ERROR: llama.cpp source not found at ${LLAMA_CPP_ROOT}" >&2
  exit 1
fi

echo "Building llama.cpp..."
cmake -S "${LLAMA_CPP_ROOT}" -B "${LLAMA_CPP_ROOT}/build"
cmake --build "${LLAMA_CPP_ROOT}/build" -j

echo "Done. llama-server binary: ${LLAMA_BIN}"
