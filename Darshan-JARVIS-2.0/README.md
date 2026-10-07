# DARSHAN JARVIS 2.0

Always-on personal AI agent for Darshan: Android remote access, Linux 24/7 server, OpenAI/Ollama, voice, images, GitHub, persistent approved memory, modular skills, VLSI, quantum/Qiskit, embedded, robotics, finance research and defensive cybersecurity.

## Safety
JARVIS is not an unrestricted shell. Actions are risk-rated:
LOW (answers/read-only), MEDIUM (build/edit), HIGH (calls/messages/Git pushes/orders), CRITICAL (financial transfer/destructive/security containment). Consequential actions require confirmation. Cybersecurity is defensive-only.

## Install
Ubuntu:
`sudo apt update && sudo apt install -y python3 python3-venv git curl sqlite3`
Rocky:
`sudo dnf install -y python3 git curl sqlite`

Then:
```bash
cd Darshan-JARVIS-2
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
nano .env
./scripts/start.sh
```

Use Tailscale on both Linux and Android for remote access. Keep JARVIS bound to 127.0.0.1 and use Tailscale Serve instead of router port forwarding.

## AI
Cloud: `AI_PROVIDER=openai` + `OPENAI_API_KEY`.
Local: `AI_PROVIDER=ollama` + `OLLAMA_MODEL`.

## Growth
JARVIS grows through approved memories, selected GitHub/local project indexing, documents, skill modules, user policies, feedback and scheduled refreshes. It does not silently rewrite its own code or security policies.

## Future adapters
Native Android controls, telephony ("call JARVIS"), broker execution, richer defensive containment, notifications and automatic project indexing.

## Offline AI + knowledge
JARVIS can run locally with Ollama, so normal inference does not require a cloud AI API. The setup script installs Ollama and downloads Qwen3.5 9B plus embeddinggemma. Live web research is optional.

The knowledge layer is retrieval-based: JARVIS can save approved notes and research results in its local knowledge database and retrieve them later. This is safer than silently retraining model weights after every question.

## Public internet access
Keep JARVIS on 127.0.0.1. Tailscale Serve is private to your tailnet; Tailscale Funnel is the public-internet option. If using Funnel, keep the JARVIS bearer token enabled, require confirmation for high-risk actions, and never expose Ollama port 11434 directly.

Example after JARVIS is running on port 8787:
```bash
tailscale funnel 8787
```

## Rocky Linux offline setup
```bash
./scripts/setup_offline_ai.sh
cp .env.example .env
openssl rand -hex 32
# put the generated value into JARVIS_ACCESS_TOKEN in .env
./scripts/start.sh
```
