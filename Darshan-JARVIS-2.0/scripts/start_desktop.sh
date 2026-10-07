#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ ! -x ".venv/bin/python" ]; then
  echo "JARVIS Python environment is missing. Run ./install.sh first."
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is missing. Run the installer again."
  exit 1
fi

if [ ! -d desktop/node_modules/electron ]; then
  echo "Installing desktop shell..."
  (cd desktop && npm install)
fi

if ! curl -fsS http://127.0.0.1:8787/health >/dev/null 2>&1; then
  echo "Starting JARVIS server..."
  nohup "$ROOT/.venv/bin/uvicorn" app.main:app --host 127.0.0.1 --port 8787 >"$ROOT/logs/jarvis.log" 2>&1 &
  echo $! >"$ROOT/logs/jarvis.pid"
  sleep 2
fi

exec npm --prefix desktop start
