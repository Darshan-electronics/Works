#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== DARSHAN JARVIS 2.0 | Ubuntu One-Command Setup ==="

if ! command -v apt-get >/dev/null 2>&1; then
  echo "This installer requires Ubuntu/Debian." >&2
  exit 1
fi

sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip python3-dev git curl wget build-essential pkg-config libssl-dev libffi-dev libxml2-dev libxslt1-dev zlib1g-dev graphviz jq unzip xdg-utils openssl

# EDA tools
sudo apt-get install -y verilator iverilog yosys || true
if ! command -v kicad-cli >/dev/null 2>&1; then
  sudo apt-get install -y software-properties-common
  sudo add-apt-repository -y ppa:kicad/kicad-10.0-releases || true
  sudo apt-get update
  sudo apt-get install -y kicad
fi

# Local AI
if ! command -v ollama >/dev/null 2>&1; then
  echo "Installing Ollama..."
  curl -fsSL https://ollama.com/install.sh | sh
fi
sudo systemctl enable --now ollama 2>/dev/null || true

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip wheel
python -m pip install -r requirements.txt
python -m pip install qiskit qiskit-aer

mkdir -p data workspace jarvis_projects logs

if [ ! -f .env ]; then
  cp .env.example .env
fi

TOKEN="$(openssl rand -hex 32)"
if grep -q '^JARVIS_ACCESS_TOKEN=' .env; then
  sed -i "s/^JARVIS_ACCESS_TOKEN=.*/JARVIS_ACCESS_TOKEN=$TOKEN/" .env
else
  printf '\nJARVIS_ACCESS_TOKEN=%s\n' "$TOKEN" >> .env
fi
unset TOKEN

# Make local-first configuration explicit.
sed -i 's/^AI_PROVIDER=.*/AI_PROVIDER=ollama/' .env
sed -i 's|^OLLAMA_BASE_URL=.*|OLLAMA_BASE_URL=http://127.0.0.1:11434|' .env
sed -i 's/^OLLAMA_MODEL=.*/OLLAMA_MODEL=qwen3.5:9b/' .env
sed -i 's/^OLLAMA_EMBED_MODEL=.*/OLLAMA_EMBED_MODEL=embeddinggemma/' .env

echo "Pulling local AI models..."
ollama pull qwen3.5:9b
ollama pull embeddinggemma || true

python -m compileall -q app

echo
echo "=== JARVIS installation complete ==="
echo "Dashboard: http://127.0.0.1:8787"
echo "Starting JARVIS..."
"$ROOT/scripts/start.sh" &
PID=$!
sleep 3

if command -v xdg-open >/dev/null 2>&1; then
  xdg-open http://127.0.0.1:8787 >/dev/null 2>&1 || true
fi

wait "$PID"
