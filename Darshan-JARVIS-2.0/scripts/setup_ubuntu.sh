#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== DARSHAN JARVIS 2.0 | Ubuntu One-Click Setup ==="
command -v apt-get >/dev/null 2>&1 || { echo "Ubuntu/Debian is required."; exit 1; }

sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip python3-dev git curl wget build-essential pkg-config libssl-dev libffi-dev libxml2-dev libxslt1-dev zlib1g-dev graphviz jq unzip xdg-utils openssl sqlite3
sudo apt-get install -y verilator iverilog yosys || true

if ! command -v kicad-cli >/dev/null 2>&1; then
  sudo apt-get install -y software-properties-common
  sudo add-apt-repository -y ppa:kicad/kicad-10.0-releases || true
  sudo apt-get update
  sudo apt-get install -y kicad || true
fi

if ! command -v ollama >/dev/null 2>&1; then
  curl -fsSL https://ollama.com/install.sh | sh
fi
if command -v systemctl >/dev/null 2>&1 && systemctl list-unit-files ollama.service >/dev/null 2>&1; then
  sudo systemctl enable --now ollama || true
fi
if ! curl -fsS http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
  nohup ollama serve >"$ROOT/logs/ollama.log" 2>&1 &
  sleep 3
fi

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip wheel
python -m pip install -r requirements.txt

mkdir -p data workspace logs
touch workspace/.gitkeep

[ -f .env ] || cp .env.example .env

python - <<'PY'
from pathlib import Path
import secrets
p=Path(".env")
lines=p.read_text().splitlines() if p.exists() else []
token=next((x.split("=",1)[1] for x in lines if x.startswith("JARVIS_ACCESS_TOKEN=") and "=" in x), "")
if not token:
    out=[]
    found=False
    for line in lines:
        if line.startswith("JARVIS_ACCESS_TOKEN="):
            out.append("JARVIS_ACCESS_TOKEN="+secrets.token_hex(32)); found=True
        else: out.append(line)
    if not found: out.append("JARVIS_ACCESS_TOKEN="+secrets.token_hex(32))
    p.write_text("\n".join(out)+"\n")
    print("Created JARVIS access token.")
else:
    print("Kept existing JARVIS access token.")
PY

ollama pull qwen3.5:9b
ollama pull embeddinggemma || true
python -m compileall -q app
python - <<'PY'
from dotenv import dotenv_values
t=dotenv_values(".env").get("JARVIS_ACCESS_TOKEN","")
print("Token configured:", bool(t), "length:", len(t))
PY

echo "KiCad CLI: $(command -v kicad-cli || echo missing)"
echo "Verilator:  $(command -v verilator || echo missing)"
echo "Icarus:     $(command -v iverilog || echo missing)"
echo "Yosys:      $(command -v yosys || echo missing)"
ollama --version
python -c "import qiskit,qiskit_aer; print('Qiskit: OK'); print('Qiskit Aer: OK')"

if ss -ltn 2>/dev/null | grep -q ':8787 '; then
  echo "JARVIS is already running."
else
  nohup "$ROOT/.venv/bin/uvicorn" app.main:app --host 127.0.0.1 --port 8787 >"$ROOT/logs/jarvis.log" 2>&1 &
  echo $! >"$ROOT/logs/jarvis.pid"
  sleep 2
fi

curl -fsS http://127.0.0.1:8787/health >/dev/null || { echo "JARVIS failed. See logs/jarvis.log"; exit 1; }
echo
echo "=== JARVIS READY ==="
echo "Open: http://127.0.0.1:8787"
command -v xdg-open >/dev/null 2>&1 && xdg-open http://127.0.0.1:8787 >/dev/null 2>&1 || true
