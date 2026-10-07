# DARSHAN JARVIS 2.0

Local-first personal engineering AI for **Ubuntu**, with a holographic JARVIS command-center dashboard.

## One-command installation

On Ubuntu:

```bash
curl -fsSL https://raw.githubusercontent.com/Darshan-electronics/Works/main/Darshan-JARVIS-2.0/scripts/bootstrap_ubuntu.sh | bash
```

The bootstrap clones/updates the repository and runs the Ubuntu setup.

The setup installs the core stack: Python/venv, FastAPI/Uvicorn, Ollama, Qwen 3.5 9B, embeddinggemma, Qiskit + Aer, KiCad/kicad-cli when available, Verilator, Icarus Verilog, Yosys, document-generation libraries, SQLite memory/knowledge, the engineering factory, quantum engine, paper-trading engine, and the dashboard.

It creates a strong local `.env` token **only if one does not already exist**, compiles the application, starts JARVIS on localhost, and opens the dashboard.

## Dashboard

Open:

```
http://127.0.0.1:8787
```

The UI is designed from the supplied orange holographic/JARVIS reference:

- black glass background
- orange/amber energy core
- animated rings and scan line
- telemetry panels
- command console
- Engineering Factory
- VLSI / ASIC workbench
- Quantum Engineering
- Paper Trading
- Knowledge / Learning

When opened locally, the dashboard obtains a session token automatically from `/ui/session`. You normally do not need to paste a token.

## Capabilities

### AI
- Local Qwen 3.5 9B chat/reasoning
- Local embeddings
- SQLite-backed knowledge and memory
- Source-backed learning
- Web research when SearXNG is configured

### Engineering Factory
A project request can generate:

- project plan JSON
- BOM CSV
- architecture SVG
- KiCad PCB draft
- DOCX report
- PDF report
- PowerPoint presentation
- validation report

PCB output is a **draft**. Verify footprints, pin mapping, ERC/DRC, power integrity and manufacturing outputs in KiCad before fabrication.

### VLSI / ASIC
The installed open-source toolchain supports workflows around:

- Verilog / SystemVerilog
- Icarus Verilog
- Verilator
- Yosys
- KiCad

OpenROAD/OpenLane, Vivado, Quartus, LTspice and vendor SDKs remain separate optional installations.

### Quantum Engineering
- quantum algorithm analysis
- Qiskit simulation
- Bell-state simulation
- quantum-VLSI partitioning
- control/readout architecture planning
- ADC/DAC and FPGA/ASIC interface planning
- cryogenic-electronics research planning

### Trading
Paper trading only by default:

- $20 paper account
- risk limits
- reward/risk checks
- paper positions
- history
- backtesting

It does not promise profits and does not place real-money orders.

### Android / voice / alerts
The repository also contains the Android companion foundation and optional voice, phone-alert and event infrastructure. These are additional setup stages after the local core is working.

## Start manually

```bash
cd ~/Works/Darshan-JARVIS-2.0
source .venv/bin/activate
./scripts/start.sh
```

Logs:

```
logs/jarvis.log
logs/ollama.log
```

## Security

JARVIS binds to `127.0.0.1:8787` by default.

Do **not** expose port 8787 or Ollama port 11434 directly to the public Internet.

For remote Android access, use a private authenticated overlay such as Tailscale. Consequential actions require confirmation, live financial execution is disabled by default, and cybersecurity functions are defensive-only.

## Repository

```
https://github.com/Darshan-electronics/Works/tree/main/Darshan-JARVIS-2.0
```
