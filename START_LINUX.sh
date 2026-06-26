#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
chmod +x "$SCRIPT_DIR"/*.sh "$SCRIPT_DIR"/scripts/*.sh "$SCRIPT_DIR"/scripts/*.py || true
if command -v python3 >/dev/null 2>&1; then
  python3 "$SCRIPT_DIR/scripts/offgrid_launcher.py" || bash "$SCRIPT_DIR/INSTALL_OFFLINE_KNOWLEDGE.sh"
else
  bash "$SCRIPT_DIR/INSTALL_OFFLINE_KNOWLEDGE.sh"
fi
