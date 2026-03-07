#!/usr/bin/env bash
set -euo pipefail

ok(){ echo "[OK] $*"; }
warn(){ echo "[WARN] $*"; }

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

for d in "$ROOT_DIR/scripts" "$ROOT_DIR/docs" "$ROOT_DIR/config" "$ROOT_DIR/zims" "$ROOT_DIR/ebooks"; do
  [[ -d "$d" ]] && ok "dir exists: $d" || warn "missing dir: $d"
done

if command -v systemctl >/dev/null 2>&1; then
  for svc in kiwix.service zim-selector.service offline-map-ui.service; do
    if systemctl is-active --quiet "$svc"; then ok "service active: $svc"; else warn "service inactive: $svc"; fi
  done
else
  warn "systemctl not available"
fi

for p in 8080 8090 8091; do
  if ss -ltn 2>/dev/null | grep -q ":$p "; then ok "port listening: $p"; else warn "port not listening: $p"; fi
done

if [[ -f "$ROOT_DIR/config/checksums.txt" ]]; then
  ok "checksums present"
else
  warn "config/checksums.txt missing"
fi

echo "doctor complete"
