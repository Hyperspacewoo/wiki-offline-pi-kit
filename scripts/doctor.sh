#!/usr/bin/env bash
set -euo pipefail

ok(){ echo "[OK] $*"; }
warn(){ echo "[WARN] $*"; }

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=/dev/null
source "${ROOT_DIR}/scripts/layout.sh"

for d in "$ROOT_DIR/scripts" "$ROOT_DIR/docs" "$ROOT_DIR/config" "$ROOT_DIR/zims" "$ROOT_DIR/ebooks"; do
  [[ -d "$d" ]] && ok "dir exists: $d" || warn "missing dir: $d"
done

for d in "$WIKI_RUNTIME_ROOT" "$WIKI_DATA_DIR" "$WIKI_MAPS_DIR" "$WIKI_ZIM_DIR"; do
  [[ -d "$d" ]] && ok "runtime dir exists: $d" || warn "runtime dir missing: $d"
done

if [[ -f /etc/default/wiki-offline-kit ]]; then
  ok "env file present: /etc/default/wiki-offline-kit"
else
  warn "env file missing: /etc/default/wiki-offline-kit"
fi

if command -v systemctl >/dev/null 2>&1; then
  for svc in kiwix.service zim-selector.service offline-map-ui.service llama-server.service; do
    if systemctl is-active --quiet "$svc"; then ok "service active: $svc"; else warn "service inactive: $svc"; fi
  done

  # service path/layout consistency checks
  if systemctl cat kiwix.service >/dev/null 2>&1; then
    systemctl cat kiwix.service | grep -q "${KIWIX_WRAPPER}" && ok "kiwix ExecStart uses kit wrapper" || warn "kiwix ExecStart not using expected wrapper (${KIWIX_WRAPPER})"
  fi
  if systemctl cat zim-selector.service >/dev/null 2>&1; then
    systemctl cat zim-selector.service | grep -q "${WIKI_KIT_ROOT}/scripts/zim_selector_ui.py" && ok "zim-ui uses kit script path" || warn "zim-ui not using expected kit script path"
  fi
  if systemctl cat offline-map-ui.service >/dev/null 2>&1; then
    systemctl cat offline-map-ui.service | grep -q "${WIKI_KIT_ROOT}/scripts/offline_map_ui.py" && ok "map-ui uses kit script path" || warn "map-ui not using expected kit script path"
  fi
  if systemctl cat llama-server.service >/dev/null 2>&1; then
    systemctl cat llama-server.service | grep -q "${LLAMA_BIN}" && ok "llama-server uses expected binary" || warn "llama-server not using expected binary (${LLAMA_BIN})"
  fi
else
  warn "systemctl not available"
fi

for p in 8080 8090 8091 8092; do
  if ss -ltn 2>/dev/null | grep -q ":$p "; then ok "port listening: $p"; else warn "port not listening: $p"; fi
done

if [[ -f "$ROOT_DIR/config/checksums.txt" ]]; then
  ok "checksums present"
else
  warn "config/checksums.txt missing"
fi

echo "doctor complete"
