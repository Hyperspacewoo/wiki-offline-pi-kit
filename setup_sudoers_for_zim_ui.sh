#!/usr/bin/env bash
set -euo pipefail

RUN_USER="$(id -un)"
SYSTEMCTL_BIN="$(command -v systemctl)"
SUDOERS_PATH="/etc/sudoers.d/zim-selector-${RUN_USER}"
TMP_FILE="$(mktemp)"

cat > "$TMP_FILE" <<EOF
# Allow ${RUN_USER} to restart/status only Kiwix services from non-interactive UI
${RUN_USER} ALL=(root) NOPASSWD: ${SYSTEMCTL_BIN} restart kiwix.service, ${SYSTEMCTL_BIN} status kiwix.service, ${SYSTEMCTL_BIN} restart zim-selector.service, ${SYSTEMCTL_BIN} status zim-selector.service
EOF

echo "Validating sudoers file..."
sudo visudo -c -f "$TMP_FILE"

echo "Installing $SUDOERS_PATH"
sudo install -m 0440 "$TMP_FILE" "$SUDOERS_PATH"
rm -f "$TMP_FILE"

echo "Done. Non-interactive restarts for kiwix/zim-selector are enabled for user: ${RUN_USER}"
