#!/usr/bin/env bash
set -euo pipefail

echo "=== DARSHAN JARVIS 2.0 — Ubuntu one-command setup ==="

if ! command -v apt-get >/dev/null 2>&1; then
  echo "This installer requires Ubuntu/Debian." >&2
  exit 1
fi

JARVIS_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$JARVIS_DIR"

sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y   python3 python3-venv python3-pip python3-dev git curl wget build-essential   pkg-config libssl-dev libffi-dev libxml2-dev libxslt1-dev zlib1g-dev   graphviz jq unzip sqlite3 xdg-utils

sudo DEBIAN_FRONTEND=noninteractive apt-get install -y verilator iverilog yosys || true

if ! command -v kicad >/dev/null 2>&1; then
  sudo apt-get install -y software-properties-common
  sudo add-apt-repository -y ppa:kicad/kicad-10.0-releases || true
  sudo apt-get update
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y kicad || true
fi

if ! command -v ollama >/dev/null 2>&1; then
  echo "Installing Ollama..."
  curl -fsSL https://ollama.com/install.sh | sh
fi

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip wheel
python -m pip install -r requirements.txt

mkdir -p data workspace logs jarvis_projects

if [ ! -f .env ]; then
  cp .env.example .env
fi

python - <<'PY'
from pathlib import Path
import secrets
p=Path(".env")
text=p.read_text() if p.exists() else ""
lines=text.splitlines()
existing=""
out=[]
for line in lines:
    if line.startswith("JARVIS_ACCESS_TOKEN="):
        existing=line.split("=",1)[1].strip()
    out.append(line)
if not existing:
    token=secrets.token_hex(32)
    if any(line.startswith("JARVIS_ACCESS_TOKEN=") for line in out):
        out=[("JARVIS_ACCESS_TOKEN="+token) if line.startswith("JARVIS_ACCESS_TOKEN=") else line for line in out]
    else:
        out.append("JARVIS_ACCESS_TOKEN="+token)
    p.write_text("\n".join(out)+"\n")
    print("Created a new local JARVIS access token.")
else:
    print("Existing JARVIS access token preserved.")
PY

if ! curl -fsS http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
  echo "Starting Ollama..."
  if command -v systemctl >/dev/null 2>&1 && systemctl list-unit-files ollama.service 2>/dev/null | grep -q '^ollama.service'; then
    sudo systemctl enable --now ollama || true
  else
    nohup ollama serve >"$JARVIS_DIR/logs/ollama.log" 2>&1 &
  fi
fi

for i in $(seq 1 20); do
  curl -fsS http://127.0.0.1:11434/api/tags >/dev/null 2>&1 && break
  sleep 1
done

ollama pull qwen3.5:9b
ollama pull embeddinggemma

python -m compileall -q app
python - <<'PY'
from dotenv import dotenv_values
t=dotenv_values(".env").get("JARVIS_ACCESS_TOKEN","")
assert len(t) >= 32, "JARVIS_ACCESS_TOKEN was not configured"
print("JARVIS token: configured")
PY

# Install a per-user systemd service so JARVIS can stay running after reboot.
mkdir -p "$HOME/.config/systemd/user"
sed "s#%h/Works/Darshan-JARVIS-2.0#$JARVIS_DIR#g" systemd/jarvis.service   > "$HOME/.config/systemd/user/jarvis.service"
systemctl --user daemon-reload || true
systemctl --user enable --now jarvis.service || true

sleep 2
if ! curl -fsS http://127.0.0.1:8787/health >/dev/null 2>&1; then
  echo "Systemd start unavailable; starting JARVIS directly..."
  nohup "$JARVIS_DIR/scripts/start.sh" >"$JARVIS_DIR/logs/jarvis.log" 2>&1 &
  sleep 2
fi

echo
echo "=== JARVIS IS READY ==="
echo "Dashboard: http://127.0.0.1:8787"
echo "Logs:      $JARVIS_DIR/logs/jarvis.log"
echo "Service:   systemctl --user status jarvis"
echo

if command -v xdg-open >/dev/null 2>&1; then
  xdg-open http://127.0.0.1:8787 >/dev/null 2>&1 &
fi
