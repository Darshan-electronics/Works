# DARSHAN JARVIS 2.0

A local-first engineering AI dashboard for Ubuntu: Ollama/Qwen, web research, persistent knowledge, VLSI/HDL tools, KiCad project generation, quantum engineering with Qiskit/Aer, paper trading, Android integration foundation, alerts/telephony adapters, and document/project artifact generation.

## One-command Ubuntu setup

Clone the repository, enter the JARVIS directory, and run the installer:

    git clone https://github.com/Darshan-electronics/Works.git
    cd Works/Darshan-JARVIS-2.0
    chmod +x scripts/*.sh
    ./scripts/install.sh

The installer installs Ubuntu dependencies, Ollama, Qwen 3.5 9B, embeddinggemma, Python dependencies, Qiskit/Aer, Verilator, Icarus Verilog, Yosys and KiCad when available; creates a strong local token; validates the application; starts JARVIS; and opens the dashboard.

Dashboard: http://127.0.0.1:8787

## Dashboard

The dashboard is a dark orange holographic/HUD-style interface inspired by the supplied JARVIS visual: a central glowing engineering core with system telemetry, VLSI/PCB controls, quantum controls, paper-trading telemetry, and authenticated local chat.

## Current capabilities

- Local Ollama/Qwen AI and embeddinggemma
- SQLite FTS5 knowledge and approved memory
- Optional SearXNG web research
- VLSI/HDL environment: KiCad, Yosys, Verilator, Icarus Verilog
- Project Factory: DOCX, PDF, PPTX, SVG architecture, BOM and KiCad PCB draft
- Quantum Engineering: Qiskit, Aer, Bell simulation and quantum-VLSI planning
- Paper trading with risk limits and history
- Android companion foundation
- Authenticated alerts and phone/voice adapters

## Trading safety

The default account is a $20 paper account. Live-money execution is not enabled. A daily profit target never forces a trade.

## Security

JARVIS binds to 127.0.0.1 by default. Do not expose Ollama port 11434 or JARVIS port 8787 directly through router port forwarding. For remote access, use an authenticated private overlay such as Tailscale.

Never commit .env, API keys, phone credentials, broker credentials, or private tokens.

## Manual start

    cd ~/Works/Darshan-JARVIS-2.0
    source .venv/bin/activate
    ./scripts/start.sh

Then open http://127.0.0.1:8787.

## Logs

    tail -f logs/jarvis.log
    tail -f logs/ollama.log

## Important limitation

JARVIS learns through retrieval and source-backed notes; it does not silently retrain model weights or rewrite its own security policy. Engineering outputs, especially PCB drafts, must be validated before fabrication.

## Ubuntu

This repository is configured for Ubuntu, not Rocky Linux. Use apt, Ubuntu paths, and scripts/install.sh.