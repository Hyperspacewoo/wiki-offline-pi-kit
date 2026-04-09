#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/layout.sh"

echo "Installing llama.cpp build deps..."
sudo apt-get update
sudo apt-get install -y build-essential cmake git

if [[ ! -d "${LLAMA_CPP_ROOT}" ]]; then
  echo "Cloning llama.cpp into ${LLAMA_CPP_ROOT}"
  git clone https://github.com/ggml-org/llama.cpp.git "${LLAMA_CPP_ROOT}"
fi

if [[ ! -f "${LLAMA_CPP_ROOT}/CMakeLists.txt" ]]; then
  echo "ERROR: llama.cpp source not found at ${LLAMA_CPP_ROOT}" >&2
  exit 1
fi

echo "Building llama.cpp..."
cmake -S "${LLAMA_CPP_ROOT}" -B "${LLAMA_CPP_ROOT}/build"
cmake --build "${LLAMA_CPP_ROOT}/build" -j

echo "Done. llama-server binary: ${LLAMA_BIN}"
