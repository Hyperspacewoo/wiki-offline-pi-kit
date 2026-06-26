#!/usr/bin/env bash
set -euo pipefail
TARGET="${1:-}"
if [[ -z "$TARGET" || ! -d "$TARGET" ]]; then
  echo "Usage: $0 /path/to/usb_mount"
  exit 1
fi
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
mkdir -p "$TARGET/OfflineKnowledgeKit"
rsync -a --exclude='.git' "$ROOT_DIR/" "$TARGET/OfflineKnowledgeKit/wiki-offline-pi-kit/"

cat > "$TARGET/INSTALL_OFFLINE_KNOWLEDGE.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
USB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "$USB_ROOT/OfflineKnowledgeKit/wiki-offline-pi-kit/INSTALL_OFFLINE_KNOWLEDGE.sh"
EOF
chmod +x "$TARGET/INSTALL_OFFLINE_KNOWLEDGE.sh"

cat > "$TARGET/START_WINDOWS.bat" <<'EOF'
@echo off
setlocal
call "%~dp0OfflineKnowledgeKit\wiki-offline-pi-kit\START_WINDOWS.bat"
EOF

cat > "$TARGET/START_LINUX.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
USB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "$USB_ROOT/OfflineKnowledgeKit/wiki-offline-pi-kit/START_LINUX.sh"
EOF
chmod +x "$TARGET/START_LINUX.sh"

cat > "$TARGET/START_MAC.command" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
USB_ROOT="$(cd "$(dirname "$0")" && pwd)"
bash "$USB_ROOT/OfflineKnowledgeKit/wiki-offline-pi-kit/START_MAC.command"
EOF
chmod +x "$TARGET/START_MAC.command"

cp -f "$ROOT_DIR/docs/START_HERE.txt" "$TARGET/" || true
echo "Bundle exported to $TARGET"
