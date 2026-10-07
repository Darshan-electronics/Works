#!/usr/bin/env bash
set -euo pipefail

echo "=== JARVIS Ubuntu installer ==="
if ! command -v apt-get >/dev/null 2>&1; then
  echo "This installer requires Ubuntu/Debian apt." >&2
  exit 1
fi

sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip python3-dev git curl wget build-essential pkg-config   libssl-dev libffi-dev libxml2-dev libxslt1-dev zlib1g-dev graphviz jq unzip

# Engineering tools available from Ubuntu repositories.
sudo apt-get install -y verilator iverilog yosys || true

# KiCad: use the official KiCad Ubuntu PPA for a current stable release.
if ! command -v kicad >/dev/null 2>&1; then
  sudo apt-get install -y software-properties-common
  sudo add-apt-repository -y ppa:kicad/kicad-10.0-releases
  sudo apt-get update
  sudo apt-get install -y kicad
fi

JARVIS_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$JARVIS_DIR"

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip wheel
python -m pip install -r requirements.txt

mkdir -p data jarvis_projects logs
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example. Set JARVIS_ACCESS_TOKEN before starting."
fi

echo
echo "=== Installed versions ==="
python --version
git --version
command -v kicad && kicad --version || true
command -v kicad-cli && kicad-cli version || true
command -v verilator && verilator --version || true
command -v iverilog && iverilog -V 2>&1 | head -n 1 || true
command -v yosys && yosys -V || true

echo
echo "JARVIS Ubuntu setup complete."
echo "Next: configure .env, install/start Ollama, then run scripts/start.sh."
