#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
chmod +x "$SCRIPT_DIR"/*.sh "$SCRIPT_DIR"/scripts/*.sh "$SCRIPT_DIR"/scripts/*.py || true
bash "$SCRIPT_DIR/INSTALL_OFFLINE_KNOWLEDGE.sh"
