#!/usr/bin/env bash
set -euo pipefail

JARVIS_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$JARVIS_DIR"

echo "================================================"
echo "       DARSHAN JARVIS 2.0 - UBUNTU SETUP"
echo "================================================"

if ! command -v apt-get >/dev/null 2>&1; then
  echo "ERROR: This installer is for Ubuntu/Debian systems." >&2
  exit 1
fi

echo "[1/8] Installing Ubuntu dependencies..."
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip python3-dev git curl wget build-essential pkg-config libssl-dev libffi-dev libxml2-dev libxslt1-dev zlib1g-dev graphviz jq unzip sqlite3

echo "[2/8] Installing VLSI/EDA tools..."
sudo apt-get install -y verilator iverilog yosys || true
if ! command -v kicad >/dev/null 2>&1; then
  sudo apt-get install -y software-properties-common
  sudo add-apt-repository -y ppa:kicad/kicad-10.0-releases || true
  sudo apt-get update
  sudo apt-get install -y kicad
fi

echo "[3/8] Creating Python environment..."
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip wheel setuptools
python -m pip install -r requirements.txt

echo "[4/8] Creating secure JARVIS configuration..."
mkdir -p data workspace logs jarvis_projects
if [ ! -f .env ]; then
  cp .env.example .env
fi
python - <<'PY'
from pathlib import Path
import secrets
p=Path(".env")
text=p.read_text() if p.exists() else ""
token=secrets.token_hex(32)
lines=text.splitlines()
found=False
out=[]
for line in lines:
    if line.startswith("JARVIS_ACCESS_TOKEN="):
        found=True
        if line.split("=",1)[1].strip():
            out.append(line)
        else:
            out.append("JARVIS_ACCESS_TOKEN="+token)
    else:
        out.append(line)
if not found:
    out.append("JARVIS_ACCESS_TOKEN="+token)
p.write_text("\n".join(out)+"\n")
print("JARVIS access token configured (kept on this machine).")
PY
chmod 600 .env

echo "[5/8] Installing local AI..."
if ! command -v ollama >/dev/null 2>&1; then
  curl -fsSL https://ollama.com/install.sh | sh
fi
sudo systemctl enable --now ollama 2>/dev/null || true
ollama pull qwen3.5:9b
ollama pull embeddinggemma

echo "[6/8] Verifying runtime..."
python -m compileall -q app
python - <<'PY'
mods=["fastapi","httpx","docx","pptx","reportlab","qiskit","qiskit_aer","pandas"]
for m in mods:
    __import__(m)
    print("[OK]",m)
PY
command -v kicad-cli >/dev/null 2>&1 && kicad-cli version || true
command -v verilator >/dev/null 2>&1 && verilator --version || true
command -v iverilog >/dev/null 2>&1 && echo "[OK] iverilog"
command -v yosys >/dev/null 2>&1 && yosys -V || true

echo "[7/8] Installing JARVIS user service..."
mkdir -p "$HOME/.config/systemd/user"
cat > "$HOME/.config/systemd/user/jarvis.service" <<EOF
[Unit]
Description=Darshan JARVIS 2.0
After=default.target

[Service]
Type=simple
WorkingDirectory=$JARVIS_DIR
EnvironmentFile=$JARVIS_DIR/.env
ExecStart=$JARVIS_DIR/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8787
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
EOF
systemctl --user daemon-reload
systemctl --user enable --now jarvis.service
systemctl --user restart jarvis.service

echo "[8/8] Opening dashboard..."
sleep 2
if curl -fsS http://127.0.0.1:8787/health >/dev/null; then
  echo
  echo "================================================"
  echo "             JARVIS IS READY"
  echo "================================================"
  echo "Dashboard: http://127.0.0.1:8787"
  echo "AI:        Ollama / Qwen 3.5 9B"
  echo "Quantum:   Qiskit + Aer"
  echo "VLSI:      KiCad + Verilator + Icarus + Yosys"
  echo
  echo "Opening browser..."
  if command -v xdg-open >/dev/null 2>&1; then
    xdg-open http://127.0.0.1:8787 >/dev/null 2>&1 || true
  fi
else
  echo "JARVIS service did not become healthy."
  echo "Check: systemctl --user status jarvis.service --no-pager"
  echo "Logs: journalctl --user -u jarvis.service -n 100 --no-pager"
  exit 1
fi
