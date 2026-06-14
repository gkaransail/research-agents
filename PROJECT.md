# Research Agents — Multi-Agent Research System

## Overview
Production-ready multi-agent system for deep research on any topic. Agents work in a pipeline — search, read, analyze, write — with real-time workflow visibility in a React dashboard.

## Architecture

```
Query → OrchestratorAgent
          ├── SearchAgent     (DuckDuckGo — free, no key)
          ├── ReaderAgent     (Jina AI reader — free)
          ├── AnalyzerAgent   (Groq LLM — free tier)
          └── WriterAgent     (Groq LLM — saves .md report)
```

## Agent Pipeline

| Step | Agent | Tool | Model |
|------|-------|------|-------|
| Plan | OrchestratorAgent | Groq LLM | llama-3.3-70b-versatile |
| Search | SearchAgent | DuckDuckGo | — |
| Read | ReaderAgent | Jina AI Reader | — |
| Analyze | AnalyzerAgent | Groq LLM | llama-3.3-70b-versatile |
| Write | WriterAgent | Groq LLM | llama-3.3-70b-versatile |

## Free APIs Used

- **Groq** — LLM inference (free tier: 30 req/min)
- **DuckDuckGo** — Web search (no API key, completely free)
- **Jina AI** — Web page content extraction (`r.jina.ai`) free tier

## Stack

| Layer | Tech |
|-------|------|
| Backend | FastAPI + Python 3.11 |
| Database | SQLite + aiosqlite (async) |
| LLM | Groq API (llama-3.3-70b-versatile / llama-3.1-8b-instant) |
| Search | duckduckgo_search |
| Reader | Jina AI Reader API |
| Real-time | WebSocket (native FastAPI) |
| Frontend | React 18 + Vite |
| Styling | Tailwind CSS |
| Markdown | react-markdown |

## Key Design Decisions

### Extensibility
- New agents: create a file in `backend/agents/`, subclass `BaseAgent`, decorate with `@register_agent("name")` — auto-discovered at startup.
- New LLM providers: add a method to `core/llm.py` LLMRouter class.
- New search tools: implement `SearchProvider` interface in `core/search.py`.

### Production Patterns
- Retry logic on all external API calls (3 retries, exponential backoff)
- Rate limiting (respects Groq free tier limits)
- Structured logging to `logs/` directory
- All workflow state persisted to SQLite (survives restarts)
- WebSocket connection manager handles multi-client broadcast

### Real-time Visibility
Every agent action emits an event:
- Stored in `workflow_events` table
- Broadcast to all WebSocket subscribers of that workflow
- Frontend shows live agent timeline with status badges

## Directory Structure

```
research_agents/
├── backend/
│   ├── main.py                 # FastAPI app, WebSocket server
│   ├── agents/
│   │   ├── base.py             # BaseAgent (subclass to add agents)
│   │   ├── registry.py         # @register_agent decorator + auto-discovery
│   │   ├── orchestrator.py     # Plans pipeline, runs agents
│   │   ├── searcher.py         # DuckDuckGo search
│   │   ├── reader.py           # Jina AI content extraction
│   │   ├── analyzer.py         # LLM synthesis
│   │   └── writer.py           # LLM report writing + .md save
│   ├── core/
│   │   ├── config.py           # Pydantic settings (env vars)
│   │   ├── database.py         # SQLite schema + CRUD
│   │   ├── llm.py              # Groq LLM router + retry
│   │   └── workflow.py         # WorkflowManager + WebSocket broadcaster
│   └── models/
│       └── schemas.py          # Pydantic request/response schemas
├── frontend/
│   └── src/
│       ├── App.jsx             # Router + layout
│       ├── api.js              # Axios API client
│       ├── components/
│       │   ├── NewResearch.jsx # Query form
│       │   ├── WorkflowList.jsx
│       │   ├── WorkflowDetail.jsx
│       │   ├── AgentTimeline.jsx  # Live event stream
│       │   └── OutputViewer.jsx   # Markdown viewer
│       └── hooks/
│           └── useWorkflow.js  # WebSocket hook
├── research_outputs/           # .md reports saved here
├── logs/
├── docker-compose.yml
└── PROJECT.md                  # This file
```

## How to Add a New Agent

1. Create `backend/agents/my_agent.py`
2. Subclass `BaseAgent` and decorate:

```python
from agents.base import BaseAgent
from agents.registry import register_agent

@register_agent("my_agent")
class MyAgent(BaseAgent):
    async def run(self, task: dict) -> dict:
        await self.emit("thinking", "Starting my task...")
        # ... do work ...
        await self.emit("completed", "Done!", data={"result": "..."})
        return {"result": "..."}
```

3. Add it to the orchestrator pipeline in `agents/orchestrator.py`

## Environment Variables

```
GROQ_API_KEY=gsk_...          # Required — get free at console.groq.com
TOGETHER_API_KEY=              # Optional fallback LLM
PRIMARY_MODEL=llama-3.3-70b-versatile
FAST_MODEL=llama-3.1-8b-instant
MAX_SEARCH_RESULTS=8
MAX_READ_URLS=5
```

## Running

```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Frontend
cd frontend && npm install && npm run dev
# Dashboard → http://localhost:5174
```

## Ports
- Backend API: `8001` (different from global_dashboard's 8000)
- Frontend: `5174`

---
*Last updated: 2026-06-14*
