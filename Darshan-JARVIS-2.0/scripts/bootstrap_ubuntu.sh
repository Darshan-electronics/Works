#!/usr/bin/env bash
set -euo pipefail

REPO="https://github.com/Darshan-electronics/Works.git"
BASE="$HOME/Works"
TARGET="$BASE/Darshan-JARVIS-2.0"

mkdir -p "$BASE"

if [ -d "$TARGET/.git" ]; then
  cd "$TARGET"
  git pull --ff-only origin main
else
  git clone --branch main "$REPO" "$TARGET"
  cd "$TARGET"
fi

exec bash scripts/setup_ubuntu.sh
