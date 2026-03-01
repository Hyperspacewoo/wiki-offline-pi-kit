#!/usr/bin/env bash
set -euo pipefail

echo "[1/5] Installing packages..."
sudo apt update
sudo apt install -y kiwix-tools python3-venv python3-pip jq

echo "[2/5] Creating folders..."
mkdir -p "$HOME/wiki/scripts" "$HOME/wiki/data" "$HOME/wiki/zim"

echo "[3/5] Creating Python venv..."
python3 -m venv "$HOME/wiki/.venv"
source "$HOME/wiki/.venv/bin/activate"
pip install --upgrade pip
pip install requests beautifulsoup4 lxml

echo "[4/5] Installing wikiask script..."
cp ./wikiask.py "$HOME/wiki/scripts/wikiask.py"
chmod +x "$HOME/wiki/scripts/wikiask.py"

echo "[5/5] Adding helper aliases to ~/.bashrc (if missing)..."
if ! grep -q "alias wiki-ask=" "$HOME/.bashrc"; then
  cat >> "$HOME/.bashrc" <<'EOF'
alias wiki-ask='source ~/wiki/.venv/bin/activate && python ~/wiki/scripts/wikiask.py'
alias wiki-start='sudo systemctl start kiwix.service'
alias wiki-stop='sudo systemctl stop kiwix.service'
alias wiki-status='systemctl status kiwix.service --no-pager && echo && journalctl -u kiwix.service -n 20 --no-pager'
EOF
fi

echo "Done. Open a new terminal or run: source ~/.bashrc"
