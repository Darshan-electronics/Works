#!/usr/bin/env bash
set -euo pipefail

echo "=== DARSHAN JARVIS 2.0 — Ubuntu one-click installer ==="

if ! command -v apt-get >/dev/null 2>&1; then
  echo "This installer requires Ubuntu/Debian." >&2
  exit 1
fi

JARVIS_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$JARVIS_DIR"

sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip python3-dev git curl wget build-essential pkg-config libssl-dev libffi-dev libxml2-dev libxslt1-dev zlib1g-dev graphviz jq unzip sqlite3 xdg-utils

sudo apt-get install -y verilator iverilog yosys || true

if ! command -v kicad >/dev/null 2>&1; then
  sudo apt-get install -y software-properties-common
  sudo add-apt-repository -y ppa:kicad/kicad-10.0-releases || true
  sudo apt-get update
  sudo apt-get install -y kicad || true
fi

if ! command -v ollama >/dev/null 2>&1; then
  echo "Installing Ollama..."
  curl -fsSL https://ollama.com/install.sh | sh
fi

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip wheel
python -m pip install -r requirements.txt

mkdir -p data workspace jarvis_projects logs

if [ ! -f .env ]; then
  cp .env.example .env
fi

python - <<'PY'
from pathlib import Path
import secrets
p=Path(".env")
text=p.read_text() if p.exists() else ""
lines=text.splitlines()
token=secrets.token_hex(32)
found=False
out=[]
for line in lines:
    if line.startswith("JARVIS_ACCESS_TOKEN="):
        out.append("JARVIS_ACCESS_TOKEN="+token)
        found=True
    else:
        out.append(line)
if not found:
    out.append("JARVIS_ACCESS_TOKEN="+token)
p.write_text("\n".join(out)+"\n")
print("JARVIS_ACCESS_TOKEN configured (secret not displayed).")
PY

echo "Preparing Ollama..."
if command -v systemctl >/dev/null 2>&1 && systemctl list-unit-files ollama.service >/dev/null 2>&1; then
  sudo systemctl enable --now ollama || true
else
  nohup ollama serve >/tmp/jarvis-ollama.log 2>&1 &
fi

sleep 2
ollama pull qwen3.5:9b
ollama pull embeddinggemma

echo
echo "=== Verification ==="
python -m compileall -q app
python - <<'PY'
from dotenv import dotenv_values
t=dotenv_values(".env").get("JARVIS_ACCESS_TOKEN","")
print("Token configured:", bool(t), "length:", len(t))
PY
ollama --version
python -c "import qiskit, qiskit_aer; print('Qiskit: OK'); print('Qiskit Aer: OK')"

echo
echo "=== Installation complete ==="
echo "Start with: ./scripts/start.sh"
echo "Dashboard: http://127.0.0.1:8787"
