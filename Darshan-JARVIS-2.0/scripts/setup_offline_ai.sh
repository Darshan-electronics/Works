#!/usr/bin/env bash
set -euo pipefail

# Local AI: no cloud model required after the model download.
# Ollama's official Linux installer: https://ollama.com/install.sh
curl -fsSL https://ollama.com/install.sh | sh
sudo systemctl enable --now ollama 2>/dev/null || true

# Practical default for a laptop/server. Upgrade later if hardware permits.
ollama pull qwen3.5:9b
ollama pull embeddinggemma

echo
 echo 'Offline AI ready.'
echo 'Test: ollama run qwen3.5:9b'
echo 'Embedding model: embeddinggemma'
