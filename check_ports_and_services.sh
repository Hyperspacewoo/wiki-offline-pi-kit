#!/usr/bin/env bash
set -euo pipefail
echo "Ports:"
ss -ltnp | grep -E ':8080|:8090|:8091' || true
echo
echo "Services:"
systemctl status kiwix.service --no-pager | sed -n '1,10p' || true
echo
systemctl status zim-selector.service --no-pager | sed -n '1,10p' || true
echo
systemctl status offline-map-ui.service --no-pager | sed -n '1,10p' || true
