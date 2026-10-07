#!/usr/bin/env bash
set -u

echo "=== JARVIS Ubuntu environment check ==="
checks=(python3 git curl ollama kicad kicad-cli verilator iverilog yosys)
for c in "${checks[@]}"; do
  if command -v "$c" >/dev/null 2>&1; then
    echo "[OK] $c -> $(command -v "$c")"
  else
    echo "[MISSING] $c"
  fi
done

echo
if command -v kicad-cli >/dev/null 2>&1; then
  echo "KiCad CLI:"
  kicad-cli version || true
fi

if command -v ollama >/dev/null 2>&1; then
  echo
  echo "Ollama models:"
  ollama list || true
fi

echo
echo "Python packages:"
if [ -x ".venv/bin/python" ]; then
  .venv/bin/python - <<'PY'
mods=["fastapi","httpx","docx","pptx","reportlab"]
for m in mods:
    try:
        __import__(m); print("[OK]",m)
    except Exception as e: print("[MISSING]",m,e)
PY
else
  echo ".venv does not exist. Run scripts/install_ubuntu.sh first."
fi
