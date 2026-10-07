# DARSHAN JARVIS 2.0

Local-first personal engineering AI for Ubuntu: JARVIS chat, VLSI/EDA workflows, quantum engineering, project/report/PPT generation, PCB drafts and validation, research/memory, and paper trading.

## One-command Ubuntu setup

    git clone https://github.com/Darshan-electronics/Works.git
    cd Works/Darshan-JARVIS-2.0
    bash scripts/install_ubuntu.sh

The installer automatically installs Ubuntu dependencies, creates the Python environment, installs engineering and quantum dependencies, installs KiCad/Verilator/Icarus/Yosys when available, installs and starts Ollama, downloads Qwen 3.5 9B and embeddinggemma, creates a secure local token, installs a user systemd service, starts JARVIS on 127.0.0.1:8787, and opens the dashboard.

Dashboard: http://127.0.0.1:8787

## Updating an existing installation

    cd ~/Works/Darshan-JARVIS-2.0
    git pull origin main
    bash scripts/install_ubuntu.sh

The installer preserves an existing non-empty .env token.

## Dashboard

The dashboard is an orange/black holographic HUD inspired by the supplied JARVIS visual: central animated neural core, system matrix, mission console, engineering factory, quantum console, knowledge acquisition and paper-trading panels.

When accessed locally, the dashboard obtains the API token through the localhost-only /ui/session endpoint. For remote access, keep the bearer token protected and use a private HTTPS/Tailscale path.

## Current capabilities

### AI
- Ollama + Qwen 3.5 9B
- local retrieval memory and knowledge
- optional web research through SearXNG
- optional cloud model fallback

### Engineering
- project planning
- DOCX, PDF and PPTX generation
- architecture diagrams
- BOM generation
- KiCad PCB draft generation
- KiCad validation hooks
- VLSI/RTL tooling integration points

### Quantum engineering
- Qiskit circuit analysis
- Qiskit Aer simulation
- Bell-state simulation
- quantum architecture planning
- quantum-VLSI/control/readout/cryogenic electronics planning

### Trading
- research and paper trading only
- OHLCV backtesting
- strategy comparison
- paper positions and history
- risk limits
- no automatic live-money execution

### Android
The Android companion can connect to the JARVIS API for notifications, calendar/device intents and future device-agent capabilities. Android still requires explicit permissions for protected capabilities.

## Security

JARVIS is deliberately not an unrestricted public shell.

- API binds to localhost by default.
- Ollama port 11434 should never be publicly exposed.
- High-risk actions require confirmation.
- Financial execution remains paper-only.
- Phone and notification features require explicit configuration.
- Never commit .env or API keys.

## Service commands

    systemctl --user status jarvis.service
    systemctl --user restart jarvis.service
    journalctl --user -u jarvis.service -n 100 --no-pager

## Manual start

    cd ~/Works/Darshan-JARVIS-2.0
    source .venv/bin/activate
    ./scripts/start.sh

## Project API

- POST /chat — JARVIS conversation
- POST /learn — research and source-backed knowledge
- POST /artifacts/project — project package generation
- POST /artifacts/validate — project/PCB validation
- GET /quantum/status — quantum backend status
- POST /quantum/analyze — quantum engineering analysis
- POST /quantum/bell — Bell-state simulation
- GET /trading/status — paper account status

## Important

The project grows through explicit modules and source-backed knowledge. It does not silently rewrite its own code, security policy or financial permissions.