#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
if [ ! -f .env ]; then cp .env.example .env; fi
python - <<'PY'
import secrets
print("Generated JARVIS token:")
print(secrets.token_urlsafe(48))
PY
echo "Edit .env, then run ./scripts/setup_offline_ai.sh and ./scripts/start.sh"
