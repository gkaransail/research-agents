# Standard Operating Procedure — Research Agents & RWA Due Diligence

## Overview

This system provides two modes:

| Mode | What it does |
|---|---|
| **Research** | Multi-agent pipeline: search → read → analyze → write `.md` report |
| **Due Diligence** | Specialist agents assess valuation, regulatory status, and risk for a real-world asset, produce a scored DD report, and optionally deploy an ERC-20 token to Ethereum |

**Stack:** FastAPI (port 8001) · React + Vite (port 5174) · Groq LLM · SQLite · web3.py

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.14 | Required for the venv |
| Node.js | 18+ | For the React frontend |
| Rust / cargo | latest | Required to build `pydantic-core` on Python 3.14 |
| Groq API key | — | Free at [console.groq.com](https://console.groq.com) |
| Hardhat node | — | Only needed for tokenization (from `rwa_platform_py`) |

---

## First-Time Setup

```bash
# 1. Install Rust (required once — skip if already installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env

# 2. Create Python virtual environment
cd backend
python3.14 -m venv .venv

# 3. Install Python dependencies
source ~/.cargo/env
PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 .venv/bin/pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and set GROQ_API_KEY=gsk_...

# 5. Install frontend dependencies
cd ../frontend
npm install
```

---

## Starting the System

Run these two commands in separate terminals from the project root.

**Terminal 1 — Backend:**
```bash
cd backend
source ~/.cargo/env
.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

Open **http://localhost:5174** in your browser.

Health check: `curl http://localhost:8001/api/agents` should return all 10 registered agents.

---

## Running a Research Workflow

1. Click **Research** in the mode toggle (top-right header).
2. Click **+ New Research**.
3. Enter a query and select depth:
   - **Fast** — 2 queries, 3 sources, ~30s
   - **Normal** — 3 queries, 5 sources, ~60s
   - **Deep** — 5 queries, 8 sources, ~2 min
4. Click **Start Research**.
5. Watch the agent timeline in real time (WebSocket updates).
6. When complete, the `.md` report opens in the viewer. Reports are saved to `research_outputs/`.

---

## Running a Due Diligence Analysis

1. Click **Due Diligence** in the mode toggle.
2. Click **+ New DD**.
3. Fill in:
   - **Asset Name** — e.g. `Marina Bay Residences Unit 2401`
   - **Asset Type** — select from dropdown
   - **Location** — e.g. `Singapore`
   - **Description** — optional brief summary
   - **Research Depth** — Standard recommended
4. Click **Run Due Diligence**.

The pipeline runs three specialist agents sequentially:

```
ValuationAgent   → market comps, price estimate
RegulatoryAgent  → ownership, zoning, compliance
RiskAgent        → market, liquidity, macro risk
DDWriterAgent    → synthesizes report + DD score (0–100) + recommendation
```

When complete, the detail panel shows the DD score and recommendation (`PROCEED` / `PROCEED WITH CAUTION` / `DO NOT PROCEED`).

---

## Tokenizing an Asset

After a DD analysis completes:

1. Click **Tokenize This Asset →** in the workflow detail panel.
2. Confirm the **Node RPC URL** (`http://127.0.0.1:8545` for local Hardhat).
3. Enter a **private key** — use a Hardhat test account key only. Never use a real wallet key.
4. Click **Deploy Token**.

The system reads tokenization parameters embedded in the DD report and deploys an `RWAToken` ERC-20 contract. On success, the panel shows:
- Contract address
- Token symbol and total supply
- Deploy transaction hash

The deployed token is immediately usable in the RWA Platform UI (`rwa_platform_py`).

> **Hardhat test key #0:** `0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80`
> Start the node with: `cd ../rwa_platform/contracts && npx hardhat node`

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/workflows` | Start a research workflow |
| `GET` | `/api/workflows` | List all workflows |
| `GET` | `/api/workflows/{id}` | Get workflow + events |
| `DELETE` | `/api/workflows/{id}` | Delete a workflow |
| `POST` | `/api/dd-workflows` | Start a DD analysis |
| `POST` | `/api/dd-workflows/{id}/tokenize` | Deploy token from DD report |
| `GET` | `/api/outputs` | List saved `.md` reports |
| `GET` | `/api/outputs/{filename}` | Read a report |
| `GET` | `/api/agents` | List registered agents |
| `WS` | `/ws/{wf_id}` | Real-time workflow events |

---

## Adding a New Agent

1. Create `backend/agents/my_agent.py`:

```python
from agents.base import BaseAgent
from agents.registry import register_agent

@register_agent("my_agent")
class MyAgent(BaseAgent):
    name = "my_agent"

    async def run(self, task: dict) -> dict:
        await self.emit("info", "Running...")
        # your logic
        return {"result": "..."}
```

2. Import it in `backend/main.py`:

```python
import agents.my_agent  # noqa
```

3. Restart the backend. The agent appears in `/api/agents`.

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `GROQ_API_KEY` | — | **Required.** Groq API key |
| `PRIMARY_MODEL` | `llama-3.3-70b-versatile` | Main LLM for analysis and writing |
| `FAST_MODEL` | `llama-3.1-8b-instant` | LLM for query planning |
| `DATABASE_PATH` | `./research_agents.db` | SQLite database path |
| `OUTPUT_DIR` | `../research_outputs` | Where `.md` reports are saved |
| `MAX_SEARCH_RESULTS` | `8` | Max results per search query |
| `REQUEST_TIMEOUT` | `30` | HTTP timeout in seconds |

---

## Troubleshooting

| Problem | Likely cause | Fix |
|---|---|---|
| Backend won't start | Missing `GROQ_API_KEY` | Set it in `backend/.env` |
| `pydantic-core` build fails | Rust not installed | Run `curl ... rustup.rs \| sh` then retry |
| No search results | DuckDuckGo rate limit | Wait 30s and retry, or reduce depth |
| Tokenize fails: "Compiled contract not found" | `RWAToken.json` missing | Run `python scripts/compile.py` in `rwa_platform_py` |
| Tokenize fails: "Cannot connect to node" | Hardhat not running | `cd ../rwa_platform/contracts && npx hardhat node` |
| Frontend blank on load | Backend not running | Start backend first, check port 8001 |
| WebSocket disconnects | Backend restarted mid-workflow | Re-open the workflow from the sidebar |

---

## File Structure

```
research_agents/
├── backend/
│   ├── agents/
│   │   ├── base.py              base class for all agents
│   │   ├── registry.py          @register_agent decorator
│   │   ├── orchestrator.py      research pipeline coordinator
│   │   ├── searcher.py          DuckDuckGo search
│   │   ├── reader.py            Jina AI URL reader
│   │   ├── analyzer.py          LLM synthesis
│   │   ├── writer.py            markdown report writer
│   │   ├── dd_orchestrator.py   DD pipeline coordinator
│   │   ├── valuation.py         market value research
│   │   ├── regulatory.py        compliance check
│   │   ├── risk.py              risk assessment
│   │   └── dd_writer.py         DD report + token params
│   ├── core/
│   │   ├── config.py            settings (env-driven)
│   │   ├── database.py          SQLite helpers
│   │   ├── deployer.py          web3.py token deployment
│   │   ├── llm.py               Groq LLM client
│   │   └── workflow.py          WebSocket + event bus
│   ├── models/schemas.py        Pydantic request/response models
│   └── main.py                  FastAPI app + all endpoints
├── frontend/src/
│   ├── App.jsx                  mode toggle + layout
│   ├── api.js                   API client
│   ├── hooks/useWorkflow.js     WebSocket hook
│   └── components/
│       ├── NewResearch.jsx
│       ├── NewDDAnalysis.jsx
│       ├── WorkflowList.jsx
│       ├── WorkflowDetail.jsx
│       ├── DDWorkflowDetail.jsx
│       ├── AgentTimeline.jsx
│       └── OutputViewer.jsx
├── research_outputs/            generated .md reports
└── SOP.md                       this file
```
