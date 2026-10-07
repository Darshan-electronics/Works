# DARSHAN JARVIS 2.0

A local-first personal engineering AI for **Ubuntu** with a holographic orange JARVIS dashboard.

## One-command install

On a fresh Ubuntu machine:

```bash
git clone https://github.com/Darshan-electronics/Works.git ~/Works
cd ~/Works/Darshan-JARVIS-2.0
bash scripts/setup_ubuntu.sh
```

The installer:

- installs the Ubuntu/Python build dependencies
- installs/updates KiCad CLI, Verilator, Icarus Verilog and Yosys where available
- installs Ollama
- creates a Python virtual environment
- installs JARVIS Python dependencies
- installs Qiskit + Qiskit Aer
- pulls Qwen 3.5 9B and embeddinggemma
- creates a local `.env` with a random bearer token if one is missing
- validates the Python source
- starts JARVIS on `127.0.0.1:8787`
- opens the dashboard automatically

After installation, open:

```
http://127.0.0.1:8787
```

If JARVIS is already running, the installer keeps the existing process and opens the dashboard.

## Dashboard

The dashboard is intentionally styled around the supplied reference: black HUD, glowing orange/gold central AI core, scan line, technical grid, telemetry panels and command tabs.

It provides:

- Command Center / JARVIS chat
- Engineering Project Factory
- VLSI / ASIC workbench
- Quantum Engineering
- Qiskit Bell-state simulation
- Paper Trading telemetry
- Research / Knowledge acquisition
- server and AI status

The browser stores the bearer token in session storage only.

## Engineering Factory

JARVIS can generate an engineering project package containing:

- project plan JSON
- BOM CSV
- architecture SVG
- PCB draft
- DOCX report
- PDF report
- PPTX presentation
- validation report

PCB output is a **draft**. Verify footprints, pin mapping, ERC/DRC, power integrity and manufacturing files before fabrication.

## VLSI / ASIC

The Ubuntu stack is prepared for:

- SystemVerilog / Verilog
- Icarus Verilog
- Verilator
- Yosys
- KiCad
- OpenROAD/OpenLane planning

Vendor tools such as Vivado, Quartus and STM32CubeIDE may require separate downloads/licensing.

## Quantum Engineering

JARVIS includes:

- Qiskit
- Qiskit Aer
- quantum algorithm analysis
- Bell-state simulation
- quantum-VLSI planning
- control/readout architecture planning
- FPGA/ASIC partitioning concepts

Hardware execution still requires the appropriate physical quantum platform.

## Trading

The current trading system is **paper trading only**. It includes a default $20 paper account, risk controls, backtesting infrastructure, paper positions and history.

It does **not** guarantee profits and does not place real-money orders.

## Security

Default network binding is localhost:

```
127.0.0.1:8787
```

Do not expose port 8787 or Ollama port 11434 directly to the public Internet. For remote Android access, use a private authenticated tunnel such as Tailscale and keep the JARVIS bearer token secret.

Consequential actions require confirmation. Phone/financial integrations remain optional.

## Useful commands

Start manually:

```bash
cd ~/Works/Darshan-JARVIS-2.0
source .venv/bin/activate
./scripts/start.sh
```

View logs:

```bash
tail -f logs/jarvis.log
```

Health check:

```bash
curl http://127.0.0.1:8787/health
```

Stop the background process created by the installer:

```bash
kill "$(cat logs/jarvis.pid)"
```

## Repository

`Darshan-JARVIS-2.0/` is the complete Ubuntu host application. The Android companion is under `android/`.
