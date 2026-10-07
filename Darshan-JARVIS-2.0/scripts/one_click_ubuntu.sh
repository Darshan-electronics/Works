#!/usr/bin/env bash
set -euo pipefail

JARVIS_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$JARVIS_DIR"

echo "=============================================="
echo " DARSHAN JARVIS 2.0 — ONE CLICK UBUNTU SETUP"
echo "=============================================="

chmod +x scripts/install_ubuntu.sh scripts/start.sh
./scripts/install_ubuntu.sh

echo
echo "Starting JARVIS..."
if pgrep -f "uvicorn app.main:app" >/dev/null 2>&1; then
  pkill -f "uvicorn app.main:app" || true
  sleep 1
fi

nohup ./scripts/start.sh > logs/jarvis.log 2>&1 &
JARVIS_PID=$!

echo "Waiting for API..."
for i in $(seq 1 60); do
  if curl -fsS http://127.0.0.1:8787/health >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! curl -fsS http://127.0.0.1:8787/health >/dev/null 2>&1; then
  echo "JARVIS did not start. Check logs/jarvis.log"
  exit 1
fi

echo
echo "JARVIS is online."
echo "Dashboard: http://127.0.0.1:8787"
echo "Log:       $JARVIS_DIR/logs/jarvis.log"
echo

if command -v xdg-open >/dev/null 2>&1; then
  xdg-open http://127.0.0.1:8787 >/dev/null 2>&1 || true
fi

echo "Press Ctrl+C to stop this setup watcher; JARVIS remains running."
wait "$JARVIS_PID"
