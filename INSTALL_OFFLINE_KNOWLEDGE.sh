#!/usr/bin/env bash
set -euo pipefail
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_BASE="$HOME/offline-knowledge"
KIT_DST="$TARGET_BASE/wiki-offline-pi-kit"
mkdir -p "$TARGET_BASE"
rsync -a --delete "$SRC_DIR/" "$KIT_DST/"
cd "$KIT_DST"
chmod +x *.sh *.py || true
./install_pi_wiki.sh
if compgen -G "$KIT_DST/*.zim" > /dev/null; then
  ./run_all_auto_zims.sh "$KIT_DST"
fi
echo "Done. Open:"
echo "  http://<HOST_IP>:8090  dashboard"
echo "  http://<HOST_IP>:8080  reader"
echo "  http://<HOST_IP>:8091  maps"
