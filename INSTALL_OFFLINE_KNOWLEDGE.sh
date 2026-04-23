#!/usr/bin/env bash
set -euo pipefail
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_BASE="$HOME/offline-knowledge"
KIT_DST="$TARGET_BASE/wiki-offline-pi-kit"
mkdir -p "$TARGET_BASE"
rsync -a --delete "$SRC_DIR/" "$KIT_DST/"
cd "$KIT_DST"
chmod +x ./*.sh ./scripts/*.sh ./scripts/*.py || true
./scripts/install_prereqs_portable.sh
./scripts/install_pi_wiki.sh
if compgen -G "$KIT_DST/zims/*.zim" > /dev/null; then
  ./scripts/run_all_auto_zims.sh "$KIT_DST/zims"
else
  echo "No bundled ZIMs found. Setting up core services anyway..."
  ./scripts/setup_zim_ui_service.sh
  ./scripts/setup_sudoers_for_zim_ui.sh
  ./scripts/setup_offline_map_service.sh
  ./scripts/setup_translator.sh || true
  ./scripts/setup_llama_cpp.sh
  ./scripts/setup_llama_service.sh || true
fi
echo "Done. Open:"
echo "  http://<HOST_IP>:8090  dashboard"
echo "  http://<HOST_IP>:8080  reader"
echo "  http://<HOST_IP>:8091  maps"
echo "  http://<HOST_IP>:8092  offline ai (llama.cpp)"
