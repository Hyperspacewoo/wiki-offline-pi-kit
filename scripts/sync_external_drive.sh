#!/usr/bin/env bash
set -euo pipefail
SRC_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DEST_BASE="${1:-/media/void/94AA7041AA7021C2/OfflineKnowledgeKit}"
DEST="$DEST_BASE/wiki-offline-pi-kit"
mkdir -p "$DEST_BASE"
rsync -a --delete "$SRC_DIR/" "$DEST/"
echo "Synced to $DEST"
