#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <mounted-drive-path> [--clean-old]"
  exit 1
fi

DRIVE_ROOT=""
CLEAN_OLD=0
for arg in "$@"; do
  case "$arg" in
    --clean-old)
      CLEAN_OLD=1
      ;;
    *)
      if [[ -z "$DRIVE_ROOT" ]]; then
        DRIVE_ROOT="$arg"
      else
        echo "Unexpected argument: $arg"
        exit 1
      fi
      ;;
  esac
done

if [[ -z "$DRIVE_ROOT" ]]; then
  echo "Mounted drive path is required."
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WIKI_KIT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DRIVE_ROOT="$(cd "$DRIVE_ROOT" && pwd)"
TARGET_ROOT="$DRIVE_ROOT/OfflineKnowledgeKit"
TARGET_KIT="$TARGET_ROOT/wiki-offline-pi-kit"

mkdir -p "$TARGET_ROOT"

echo "== Syncing working kit to external drive =="
rsync -a --delete --delete-excluded \
  --exclude='.git/' \
  --exclude='__pycache__/' \
  --exclude='*.pyc' \
  "$WIKI_KIT_ROOT/" "$TARGET_KIT/"

cat > "$DRIVE_ROOT/INSTALL_OFFLINE_KNOWLEDGE.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
USB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "$USB_ROOT/OfflineKnowledgeKit/wiki-offline-pi-kit/INSTALL_OFFLINE_KNOWLEDGE.sh"
EOF
chmod +x "$DRIVE_ROOT/INSTALL_OFFLINE_KNOWLEDGE.sh"

cat > "$DRIVE_ROOT/START_WINDOWS.bat" <<'EOF'
@echo off
setlocal
call "%~dp0OfflineKnowledgeKit\wiki-offline-pi-kit\START_WINDOWS.bat"
EOF

cat > "$DRIVE_ROOT/START_LINUX.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
USB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "$USB_ROOT/OfflineKnowledgeKit/wiki-offline-pi-kit/START_LINUX.sh"
EOF
chmod +x "$DRIVE_ROOT/START_LINUX.sh"

cat > "$DRIVE_ROOT/START_MAC.command" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
USB_ROOT="$(cd "$(dirname "$0")" && pwd)"
bash "$USB_ROOT/OfflineKnowledgeKit/wiki-offline-pi-kit/START_MAC.command"
EOF
chmod +x "$DRIVE_ROOT/START_MAC.command"

cat > "$DRIVE_ROOT/START_HERE.txt" <<'EOF'
OFFGRID KIT
===========

Primary kit location:
- OfflineKnowledgeKit/wiki-offline-pi-kit

Recommended launchers:
- Windows:     START_WINDOWS.bat
- Linux:       START_LINUX.sh
- macOS:       START_MAC.command

This drive copy is intended to be the single working offline kit.
EOF

if [[ "$CLEAN_OLD" == "1" ]]; then
  echo "== Cleaning known stale copies from drive =="
  for path in \
    "$DRIVE_ROOT/wiki-offline-20260422-195014" \
    "$DRIVE_ROOT/OfflineKnowledgeKit/pi-wiki-kit"
  do
    if [[ -e "$path" ]]; then
      gio trash "$path"
      echo "Moved to trash: $path"
    fi
  done
fi

echo "== Stage complete =="
echo "Drive root: $DRIVE_ROOT"
echo "Kit path:   $TARGET_KIT"
