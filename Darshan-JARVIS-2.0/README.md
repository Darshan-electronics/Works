# DARSHAN JARVIS 2.0

Always-on personal AI agent for Darshan: Android remote access, Linux 24/7 server, OpenAI/Ollama, voice, images, GitHub, persistent approved memory, modular skills, VLSI, quantum/Qiskit, embedded, robotics, finance research and defensive cybersecurity.

## Safety
JARVIS is not an unrestricted shell. Actions are risk-rated:
LOW (answers/read-only), MEDIUM (build/edit), HIGH (calls/messages/Git pushes/orders), CRITICAL (financial transfer/destructive/security containment). Consequential actions require confirmation. Cybersecurity is defensive-only.

## Install
Ubuntu:
`sudo apt update && sudo apt install -y python3 python3-venv git curl sqlite3`
Ubuntu:
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

## Ubuntu setup

JARVIS is designed for Ubuntu. Install the base dependencies with:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git curl sqlite3
```

For the complete engineering environment, use:

```bash
chmod +x scripts/install_ubuntu.sh scripts/check_ubuntu.sh
./scripts/install_ubuntu.sh
./scripts/check_ubuntu.sh
```

# put the generated value into JARVIS_ACCESS_TOKEN in .env
./scripts/start.sh
```

## Learning pipeline

JARVIS now has a real retrieval-based learning loop:

1. `POST /chat` searches approved memories and the local FTS5 knowledge base before answering.
2. `POST /learn` searches SearXNG, asks the local model to curate the evidence, stores the resulting note and source URLs, and makes it retrievable later.
3. `GET /knowledge?q=...` lets the UI inspect stored knowledge.
4. `GET /memory?q=...` lets the UI inspect approved memories.

This is knowledge acquisition, not automatic weight retraining. SQLite FTS5 provides local full-text retrieval and relevance ranking. citeturn0search0

### Start it

If the repository was cloned into `~/Darshan-JARVIS-2.0`:

```bash
cd ~/Darshan-JARVIS-2.0
bash scripts/install.sh
# Edit .env and put a strong random value in JARVIS_ACCESS_TOKEN
bash scripts/setup_offline_ai.sh
bash scripts/start.sh
```

The local server listens only on `127.0.0.1:8787`. Do not expose Ollama's `11434` port.

### Make it reachable from anywhere

Install Tailscale on the Linux PC and Android phone, then for a public HTTPS endpoint use:

```bash
tailscale funnel 8787
```

Keep the bearer token enabled. A public endpoint should never be unauthenticated. For private access, prefer Tailscale Serve instead of Funnel.

### First learning test

Open JARVIS, enter the token, and ask:

```
Teach yourself the current OpenLane 2 architecture. Research it,
separate facts from uncertain claims, save the useful knowledge,
and cite the sources when you answer me later.
```

Then ask a follow-up question about OpenLane 2. JARVIS will search its local knowledge store before answering.

### Important limitation

JARVIS does not silently rewrite its own code, model weights, security rules, or financial permissions as a result of research. Learning is stored as source-backed knowledge and approved memory. This keeps the system upgradeable without turning every web result into permanent trusted truth.

## Android device agent + college

The planned Android companion is the device bridge for JARVIS. It can use Android intents for supported cross-app actions and request individual permissions for protected data. Android's application sandbox means there is no safe universal "all apps, all data" permission; capabilities must be granted individually. citeturn0search0turn0search9

The design is documented in `docs/ANDROID_DEVICE_AGENT.md`. It includes a College Setup wizard for timetable, college timings, rooms, faculty, exams, attendance rules and official portal links.

For calendar integration, Android exposes calendar data through its Calendar provider when the app has the appropriate permission. citeturn0search2turn0search12

For deeper UI automation, an optional Android AccessibilityService can be used only after the user explicitly enables it in Settings; Android requires that explicit user action. citeturn0search1


## Ubuntu host

JARVIS is designed to run on Ubuntu. Use `scripts/install_ubuntu.sh` for the base engineering environment and `scripts/check_ubuntu.sh` to verify dependencies. The setup targets Python, Ollama, KiCad/kicad-cli, Verilator, Icarus Verilog and Yosys. KiCad recommends its Ubuntu PPA for current stable releases.\n

## Quantum engineering

JARVIS includes a quantum-engineering layer for quantum circuit/algorithm planning, local simulation when Qiskit/Qiskit Aer is installed, quantum-system analysis, and quantum-VLSI planning that connects qubit/control/readout requirements with ADC/DAC, RF/microwave, FPGA/ASIC, cryogenic-electronics and verification workflows. Quantum SDKs are optional and remain disabled unless installed. Hardware execution should require explicit configuration and confirmation.\n