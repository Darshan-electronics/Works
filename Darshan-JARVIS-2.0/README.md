# DARSHAN JARVIS 2.0

Local-first personal engineering AI for Ubuntu: JARVIS chat, engineering project generation, VLSI/ASIC workflows, PCB drafts and validation, quantum engineering/Qiskit, paper trading, knowledge acquisition, Android events and optional voice/phone integrations.

## One-command Ubuntu setup

From the repository root:

```bash
bash scripts/setup_ubuntu.sh
```

The installer installs Ubuntu dependencies with apt, KiCad/Verilator/Icarus/Yosys, Ollama, the Python environment, Qiskit + Aer, Qwen 3.5 9B and embeddinggemma; creates a strong local .env token; compiles the app; starts JARVIS on 127.0.0.1:8787; and opens the dashboard.

Dashboard: `http://127.0.0.1:8787`

If already cloned:

```bash
cd ~/Works/Darshan-JARVIS-2.0
git pull origin main
bash scripts/setup_ubuntu.sh
```

Do not run `ollama serve` manually if the Ollama service is already running.

## Dashboard

The dashboard is a dark orange holographic JARVIS interface inspired by the supplied visual reference. It includes an animated core/orb, command center, AI/server telemetry, JARVIS chat, Engineering Factory, VLSI/ASIC workbench, Quantum Engineering, Paper Trading, Knowledge/Learning and event/capability panels.

The browser stores the bearer token only in session storage. The API remains bound to localhost by default.

## Engineering Factory

A project request can generate a project plan JSON, BOM CSV, architecture SVG, PCB draft, DOCX report, PDF report, PPTX presentation and validation report. PCB output is a draft and must be checked in KiCad before fabrication.

## Quantum Engineering

JARVIS includes circuit/algorithm analysis, Bell-state simulation, quantum hardware planning and quantum-VLSI partitioning covering control/readout, ADC/DAC, FPGA/ASIC and cryogenic-electronics planning. Hardware execution is not automatic.

## VLSI / electronics

The Ubuntu installer targets KiCad/kicad-cli, Verilator, Icarus Verilog and Yosys. OpenROAD/OpenLane, Vivado, Quartus, LTspice, STM32CubeIDE and vendor SDKs can be installed separately where licensing/platform requirements apply.

## Trading

JARVIS currently uses paper trading only: a default $20 paper account, risk limits, reward/risk checks, paper positions, history and backtest infrastructure. It does not promise daily profits and does not place real-money orders.

## Remote Android access

Use Tailscale for remote access and keep JARVIS bound to localhost. Prefer a private Tailscale network/Serve endpoint. Never expose Ollama port 11434 directly.

## Security

JARVIS is not an unrestricted shell agent. Consequential actions require confirmation; financial execution is disabled by default; manual phone calls require confirmation; critical alerts use urgency/cooldowns; cybersecurity is defensive-only; secrets stay in .env and are ignored by Git.

## Optional integrations

GitHub, ElevenLabs voice, Twilio phone alerts, SearXNG web research and OpenAI cloud fallback can be configured later. Local Ollama operation does not require an OpenAI API key.

The repository is the software stack; you must run the installer on the Ubuntu machine.