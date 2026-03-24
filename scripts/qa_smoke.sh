#!/usr/bin/env bash
set -euo pipefail

HOST="${HOST:-127.0.0.1}"
UI_PORT="${UI_PORT:-8090}"
KIWIX_PORT="${KIWIX_PORT:-8080}"
MAP_PORT="${MAP_PORT:-8091}"
TIMEOUT="${TIMEOUT:-8}"
RUN_ADMIN_ACTIONS=0

if [[ "${1:-}" == "--admin-actions" ]]; then
  RUN_ADMIN_ACTIONS=1
fi

pass=0
fail=0

ok(){ echo "[PASS] $*"; pass=$((pass+1)); }
no(){ echo "[FAIL] $*"; fail=$((fail+1)); }

check_cmd(){
  if command -v "$1" >/dev/null 2>&1; then
    ok "dependency present: $1"
  else
    no "missing dependency: $1"
  fi
}

check_service(){
  local svc="$1"
  if ! command -v systemctl >/dev/null 2>&1; then
    echo "[WARN] systemctl unavailable; skipped service check: $svc"
    return
  fi
  if systemctl is-active --quiet "$svc"; then
    ok "service active: $svc"
  else
    no "service inactive: $svc"
  fi
}

check_port(){
  local p="$1"
  if ss -ltn 2>/dev/null | grep -q ":$p "; then
    ok "port listening: $p"
  else
    no "port not listening: $p"
  fi
}

http_code(){
  local url="$1"
  curl -sS -o /dev/null -m "$TIMEOUT" -w "%{http_code}" "$url" || echo "000"
}

check_http_2xx(){
  local name="$1"
  local url="$2"
  local code
  code="$(http_code "$url")"
  if [[ "$code" =~ ^2 ]]; then
    ok "$name reachable ($code): $url"
  else
    no "$name not reachable ($code): $url"
  fi
}

check_http_redirect(){
  local name="$1"
  local url="$2"
  local code
  code="$(http_code "$url")"
  if [[ "$code" =~ ^30[1278]$ ]]; then
    ok "$name redirect works ($code): $url"
  else
    no "$name redirect failed ($code): $url"
  fi
}

check_header_contains(){
  local name="$1"
  local url="$2"
  local expected="$3"
  if curl -sS -D - -o /dev/null -m "$TIMEOUT" "$url" | tr -d '\r' | grep -Eiq "$expected"; then
    ok "$name header contains '$expected'"
  else
    no "$name missing header '$expected'"
  fi
}

check_admin_action(){
  local action="$1"
  local url="http://${HOST}:${UI_PORT}/api/admin/action"
  local payload
  payload="{\"action\":\"${action}\"}"
  local body
  body="$(curl -sS -m 60 -H 'Content-Type: application/json' -d "$payload" "$url" || true)"
  if echo "$body" | grep -q '"ok":true'; then
    ok "admin action succeeded: $action"
  else
    no "admin action failed: $action ($(echo "$body" | tr '\n' ' ' | cut -c1-180))"
  fi
}

echo "== QA smoke checks =="
check_cmd curl
check_cmd ss

echo
check_service kiwix.service
check_service zim-selector.service
check_service offline-map-ui.service

echo
check_port "$KIWIX_PORT"
check_port "$UI_PORT"
check_port "$MAP_PORT"

echo
check_http_2xx "Dashboard" "http://${HOST}:${UI_PORT}/"
check_http_2xx "Setup page" "http://${HOST}:${UI_PORT}/setup"
check_http_2xx "Health endpoint" "http://${HOST}:${UI_PORT}/health"
check_http_2xx "Kiwix" "http://${HOST}:${KIWIX_PORT}/"
check_http_2xx "Offline map" "http://${HOST}:${MAP_PORT}/"

echo
check_http_redirect "Open Knowledge button" "http://${HOST}:${UI_PORT}/go/knowledge"
check_http_redirect "Open Maps button" "http://${HOST}:${UI_PORT}/go/maps"
check_http_redirect "Open Translate button" "http://${HOST}:${UI_PORT}/go/translate"
check_http_redirect "Open Library button" "http://${HOST}:${UI_PORT}/go/library"
check_http_redirect "Quick Action: Water" "http://${HOST}:${UI_PORT}/go/water"
check_http_redirect "Quick Action: First Aid" "http://${HOST}:${UI_PORT}/go/firstaid"
check_http_redirect "Quick Action: Shelter" "http://${HOST}:${UI_PORT}/go/shelter"
check_http_redirect "Quick Action: Emergency Phrase" "http://${HOST}:${UI_PORT}/go/emergency-phrase"

echo
check_header_contains "Dashboard cache control" "http://${HOST}:${UI_PORT}/" "^Cache-Control:.*no-cache|^Cache-Control:.*no-store"
check_header_contains "Dashboard pragma" "http://${HOST}:${UI_PORT}/" "^Pragma:.*no-cache"

if [[ "$RUN_ADMIN_ACTIONS" -eq 1 ]]; then
  echo
  check_admin_action doctor
  check_admin_action verify
fi

echo
echo "Smoke summary: ${pass} passed, ${fail} failed"
if [[ "$fail" -gt 0 ]]; then
  exit 1
fi
