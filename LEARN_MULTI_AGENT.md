# How to Build Multi-Agent Systems from Scratch
### A step-by-step guide for LangChain / CrewAI / n8n developers

> Study path through the `research_agents` codebase.
> Each step maps what you already know from frameworks to what's happening in raw code.

---

## Before You Start: The Mental Model Shift

When you use LangChain, CrewAI, or n8n, the framework hides a lot of plumbing.
This codebase does the same things — but in the open, so you can see every wire.

| What you know | What it maps to here | File |
|---|---|---|
| `CrewAI Agent` | `BaseAgent` subclass | `agents/base.py` |
| `CrewAI Crew` | `OrchestratorAgent` | `agents/orchestrator.py` |
| `CrewAI Task` | `task: dict` passed to `agent.run()` | everywhere |
| `LangChain Tool` | any method an agent calls (search, read, llm) | `agents/searcher.py` |
| `LangChain AgentExecutor` | the `while` loop inside `orchestrator.run()` | `orchestrator.py:17` |
| `LangChain Callbacks` | `self.emit(event_type, message)` | `agents/base.py:16` |
| `LangChain Memory` | `WorkflowManager` + SQLite events table | `core/workflow.py` |
| `n8n Workflow` | `WorkflowManager` (tracks state + emits events) | `core/workflow.py:47` |
| `n8n Node` | `BaseAgent` subclass | `agents/base.py` |
| `n8n Execution Log` | `workflow_events` table in SQLite | `core/database.py` |
| `n8n WebSocket updates` | `ConnectionManager.broadcast()` | `core/workflow.py:32` |

The key insight: **frameworks are just opinionated wrappers around these same primitives.**
Once you understand the primitives, you can build (or replace) any framework yourself.

---

## Step 1 — The Contract: What is an Agent?

**File:** `backend/agents/base.py` (all 23 lines — read them all)

This is the most important file. Everything else builds on it.

```python
# base.py:5-22
class BaseAgent(ABC):
    name: str = "base"

    def __init__(self, wf: WorkflowManager):
        self.wf = wf                          # ← shared event bus (like n8n's execution context)

    async def emit(self, event_type, message, data=None):
        await self.wf.emit(self.name, ...)    # ← broadcasts to WebSocket + saves to DB

    @abstractmethod
    async def run(self, task: dict) -> dict:  # ← THE CONTRACT: in goes a task, out comes a result
        ...
```

**What to learn here:**
- Every agent is just a class with one method: `run(task) → dict`
- `task` is a plain dict — it carries the input (query, urls, analysis, etc.)
- `result` is a plain dict — it carries the output to the next agent
- `self.emit()` is how the agent narrates what it's doing (replaces framework callbacks)

**CrewAI equivalent:** In CrewAI you define `Agent(role=..., goal=..., tools=[...])` and assign it a `Task`. Here the role and goal live inside `run()` as the system prompt. The task is passed directly.

**LangChain equivalent:** In LangChain you call `agent_executor.invoke({"input": ...})`. Here you call `agent.run({"query": ...})`. Same idea, no magic.

---

## Step 2 — The Registry: How Agents Are Discovered

**File:** `backend/agents/registry.py` (31 lines)

```python
# registry.py:16-20
def register_agent(name: str):
    def decorator(cls):
        _REGISTRY[name] = cls    # ← stores class in a dict
        return cls
    return decorator
```

Usage on any agent:
```python
@register_agent("searcher")      # ← one decorator, agent is now in the system
class SearchAgent(BaseAgent):
    ...
```

**What to learn here:**
- This is the Python decorator pattern used as a plugin system
- `_REGISTRY` is just a `dict[str, class]` — simple as it gets
- When `main.py` imports the agent files, the decorators run, agents self-register
- `list_agents()` at line 29 is why the UI can show "5 agents registered" on startup

**CrewAI equivalent:** In CrewAI you pass `agents=[researcher, writer]` to `Crew()`. Here you just import the files — the registry fills automatically.

**Why this matters for expandability:** To add a new agent, you touch zero existing files except one import in `main.py`. The rest of the system discovers it automatically.

---

## Step 3 — The LLM Wrapper: One Place for All Model Calls

**File:** `backend/core/llm.py` (49 lines)

```python
# llm.py:20-43
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),  # ← 2s, 4s, 8s... retry backoff
)
async def chat(self, messages, model=None, temperature=0.7, max_tokens=4096) -> str:
    model = model or settings.PRIMARY_MODEL
    response = await self.groq.chat.completions.create(...)
    return response.choices[0].message.content           # ← always returns a plain string
```

**What to learn here:**
- Wrap your LLM client in one class. Every agent calls `llm.chat()`, not the SDK directly
- The `@retry` decorator (from `tenacity`) handles Groq rate limits automatically — 3 retries, exponential backoff
- `fast_chat()` at line 45 uses a cheaper/faster model for quick tasks (query planning)
- This is where you'd add OpenAI, Ollama, Together AI as fallbacks — one place, all agents benefit

**LangChain equivalent:** `ChatGroq(...)` or any `BaseChatModel`. The difference: LangChain wraps the response in a `BaseMessage` object. Here it's just a string — simpler to work with.

**Key pattern:** Always abstract the LLM behind one function. When you swap models, you change one file, not ten agents.

---

## Step 4 — A Tool-Only Agent (No LLM)

**File:** `backend/agents/searcher.py` (54 lines)

```python
# searcher.py:9-44
@register_agent("searcher")
class SearchAgent(BaseAgent):
    name = "searcher"

    async def run(self, task: dict) -> dict:
        queries = task.get("queries", [task.get("query", "")])  # ← unpack input

        await self.emit("searching", f"Searching {len(queries)} queries...")  # ← narrate

        for query in queries:
            results = await asyncio.to_thread(self._search, query, max_results)
            # asyncio.to_thread ← runs sync DuckDuckGo library in a thread pool
            #                       so it doesn't block the async event loop

        return {"results": all_results}  # ← clean output dict

    def _search(self, query, max_results):       # ← the actual tool (sync)
        with DDGS() as ddgs:
            raw = list(ddgs.text(query, max_results=max_results))
        return [{"title": ..., "url": ..., "snippet": ...} for r in raw]
```

**What to learn here:**
- This agent has NO LLM — it's purely a tool wrapper
- `asyncio.to_thread()` at line 25 is how you run sync libraries (like DuckDuckGo) inside async code
- `emit()` calls between steps are how the frontend gets live updates
- Input comes in via `task` dict, output goes out via return dict — strict interface

**LangChain equivalent:** A `Tool` with `func=ddg_search`. Here it's an agent class instead of a function, because it needs to emit events and handle multiple queries.

**n8n equivalent:** An HTTP Request node or Search node. Here you write the node logic yourself.

---

## Step 5 — An LLM-Powered Agent

**File:** `backend/agents/analyzer.py` (65 lines)

```python
# analyzer.py:6-53
@register_agent("analyzer")
class AnalyzerAgent(BaseAgent):
    name = "analyzer"

    async def run(self, task: dict) -> dict:
        query   = task["query"]
        pages   = task.get("pages", [])           # ← output from ReaderAgent
        
        await self.emit("analyzing", f"Synthesizing {len(pages)} sources...")

        source_text = self._build_source_text(pages, search_results)  # ← format for LLM

        analysis = await llm.chat(
            messages=[
                {"role": "system", "content": "You are an expert research analyst..."},
                {"role": "user",   "content": f"Query: {query}\n\nSources:\n{source_text}\n\n..."},
            ],
            temperature=0.3,      # ← low temp = factual, deterministic
            max_tokens=3000,
        )

        return {"analysis": analysis, "sources_used": len(pages)}
```

**What to learn here:**
- The LLM call is just `messages = [system, user]` → `llm.chat()` → string back
- `temperature=0.3` for analysis (factual), `0.7` for creative writing — this is prompt engineering
- The agent's "intelligence" is entirely in how you format `source_text` and write the system prompt
- No LangChain chains, no prompt templates — just f-strings and a list of dicts

**LangChain equivalent:** `LLMChain(llm=..., prompt=ChatPromptTemplate(...))`. Here it's just `llm.chat(messages=[...])`. Same result, no abstraction overhead.

**The key insight:** LangChain Chains are just a structured way to call `llm(messages)`. Once you understand that, you don't need the Chain class — you can write the logic directly.

---

## Step 6 — The Event Bus: How Agents Talk to the World

**File:** `backend/core/workflow.py` (88 lines) — the most important infrastructure file

There are two classes here. Read them both carefully.

### Part A: ConnectionManager (lines 15–44)

```python
# workflow.py:15-41
class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, list[WebSocket]] = {}
        #                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^
        #                  workflow_id → list of connected browsers

    async def connect(self, workflow_id, ws):
        await ws.accept()
        self._connections.setdefault(workflow_id, []).append(ws)

    async def broadcast(self, workflow_id, message):
        for ws in self._connections.get(workflow_id, []):
            await ws.send_text(json.dumps(message))   # ← push to every connected browser
```

This is how the live agent timeline works in the UI. When an agent calls `emit()`, this class pushes it to every browser tab watching that workflow.

**n8n equivalent:** n8n's execution log panel. Except here you build it yourself.

### Part B: WorkflowManager (lines 47–87)

```python
# workflow.py:47-80
class WorkflowManager:
    def __init__(self, workflow_id):
        self.workflow_id = workflow_id

    async def emit(self, agent_name, event_type, message, data=None):
        # 1. Save to DB (persistent, survives restarts)
        await db.insert_event(ev_id, self.workflow_id, agent_name, event_type, message, data, ts)

        # 2. Broadcast to all connected WebSockets (real-time)
        await manager.broadcast(self.workflow_id, payload)

        # 3. Log to terminal
        logger.info(f"[{agent_name}] {event_type}: {message}")
```

**What to learn here:**
- Every `emit()` does three things atomically: persists, broadcasts, logs
- This is why closing and reopening the browser still shows all events — they're in SQLite
- The `WorkflowManager` instance is passed DOWN to every agent (dependency injection)
- This is the equivalent of LangChain's `CallbackManager` — but you own the code

**LangChain equivalent:** `BaseCallbackHandler` with `on_agent_action`, `on_tool_start`, etc. Here you call `emit()` yourself whenever you want — more explicit, more control.

---

## Step 7 — The Orchestrator: How Agents Coordinate

**File:** `backend/agents/orchestrator.py` (104 lines) — this is your "Crew"

```python
# orchestrator.py:13-71
@register_agent("orchestrator")
class OrchestratorAgent(BaseAgent):
    name = "orchestrator"

    async def run(self, task: dict) -> dict:
        query = task["query"]

        # Step 1: LLM plans which searches to run
        queries = await self._plan_queries(query, depth)       # ← LLM call

        # Step 2: Delegate to SearchAgent
        searcher = SearchAgent(self.wf)                        # ← pass down the event bus
        search_output = await searcher.run({"queries": queries})

        # Step 3: Delegate to ReaderAgent
        reader = ReaderAgent(self.wf)
        read_output = await reader.run({"urls": urls})

        # Step 4: Delegate to AnalyzerAgent
        analyzer = AnalyzerAgent(self.wf)
        analysis_output = await analyzer.run({"query": query, "pages": pages})

        # Step 5: Delegate to WriterAgent
        writer = WriterAgent(self.wf)
        write_output = await writer.run({"query": query, "analysis": analysis})

        return write_output
```

**What to learn here:**
- The orchestrator IS the crew — it knows the pipeline, creates sub-agents, passes outputs as inputs
- `self.wf` (WorkflowManager) is passed to every sub-agent — they all share the same event bus
- Data flows as plain dicts: `search_output["results"]` → `read_output["pages"]` → `analysis_output["analysis"]` → final report
- Each step's output becomes the next step's input — this is the data pipeline pattern

**CrewAI equivalent:**
```python
# CrewAI way
crew = Crew(agents=[searcher, reader, analyzer, writer], tasks=[...], process=Process.sequential)
crew.kickoff()

# Our way
orchestrator.run({"query": query})   # ← same thing, explicit code
```

**LangChain equivalent:** `SequentialChain` or a custom `AgentExecutor` with tool routing. Here it's just Python function calls in order.

**The planning step** at `orchestrator.py:73-103`:
```python
async def _plan_queries(self, query, depth) -> list[str]:
    resp = await llm.fast_chat(messages=[
        {"role": "system", "content": "Return exactly N queries as a JSON array. No explanation."},
        {"role": "user",   "content": f"Generate queries to research: {query}"},
    ])
    # Parse JSON out of LLM response
    start = resp.find("[")
    end   = resp.rfind("]") + 1
    return json.loads(resp[start:end])
```

This is **structured output** — you tell the LLM to return JSON and parse it yourself. LangChain's `JsonOutputParser` does the same thing. The key: constrain the format in the system prompt, parse the brackets yourself as a fallback.

---

## Step 8 — The Glue: How the API Triggers the Pipeline

**File:** `backend/main.py` — focus on two parts

### Part A: How a research job starts (lines 44–49)

```python
# main.py:44-49
@app.post("/api/workflows")
async def start_research(body: WorkflowCreate, background_tasks: BackgroundTasks):
    wf_id = await create_workflow(body.query)          # ← create DB record
    background_tasks.add_task(_run_research, wf_id, ...) # ← run pipeline in background
    return WorkflowListItem(...)                        # ← return immediately to frontend
```

`BackgroundTasks` is FastAPI's built-in way to run async work without blocking the HTTP response. The frontend gets the `workflow_id` immediately, then subscribes to the WebSocket to watch it run.

### Part B: The background task (lines 129–141)

```python
# main.py:129-141
async def _run_research(wf_id, query, depth):
    wf = WorkflowManager(wf_id)          # ← create the event bus for this workflow
    await wf.set_status("running")

    orchestrator = OrchestratorAgent(wf) # ← inject the event bus
    result = await orchestrator.run({"query": query, "depth": depth})

    await wf.set_status("completed", result.get("output_file"))
    # ↑ this broadcast reaches the browser via WebSocket
```

### Part C: WebSocket endpoint (lines 106–124)

```python
# main.py:106-124
@app.websocket("/ws/{wf_id}")
async def websocket_endpoint(websocket, wf_id):
    await manager.connect(wf_id, websocket)

    # Catch-up: send all past events to late subscribers
    events = await db.get_workflow_events(wf_id)
    for ev in events:
        await websocket.send_text(json.dumps({"type": "event", "event": ev}))

    while True:
        await websocket.receive_text()  # keep alive (browser sends nothing, just pings)
```

**What to learn here:**
- HTTP POST creates the workflow and returns immediately
- WebSocket delivers live updates while it runs
- Past events are replayed on connect — so refreshing the page still shows everything
- `manager` (ConnectionManager) is a module-level singleton — one instance, shared by all requests

---

## Step 9 — The Database: Workflow Memory

**File:** `backend/core/database.py`

The schema is 3 tables (see lines 8–17 in CREATE_SQL):

```sql
workflows (id, query, status, created_at, updated_at, output_file)
workflow_events (id, workflow_id, agent_name, event_type, message, data, timestamp)
```

**What to learn here:**
- `workflow_events` is your agent memory — every `emit()` call writes a row
- This is what LangChain calls "chat history" or "memory buffer" — just a table of timestamped messages
- Because it's in SQLite, it survives server restarts — workflows that were "running" are visible even after a crash
- `get_workflow_events(wf_id)` at line 58 is what the WebSocket replays on reconnect

---

## Step 10 — Reading Order Summary

Study the files in this order. Each one is short enough to read in full.

```
1.  agents/base.py         ← 23 lines  — the contract every agent follows
2.  agents/registry.py     ← 31 lines  — how agents self-register
3.  core/config.py         ← 20 lines  — env vars and settings
4.  core/llm.py            ← 49 lines  — LLM wrapper with retry
5.  core/database.py       ← 85 lines  — SQLite CRUD (read schema first)
6.  core/workflow.py       ← 88 lines  — event bus + WebSocket broadcaster
7.  agents/searcher.py     ← 54 lines  — tool-only agent (no LLM)
8.  agents/reader.py       ← 60 lines  — async HTTP + content extraction
9.  agents/analyzer.py     ← 65 lines  — LLM agent with structured prompt
10. agents/writer.py       ← 105 lines — LLM agent that saves a file
11. agents/orchestrator.py ← 104 lines — multi-agent coordinator
12. main.py                ← 141 lines — FastAPI server + WebSocket + trigger
```

**Total: ~725 lines.** That's a complete, production-grade multi-agent system.
LangChain is ~80,000 lines. CrewAI is ~5,000. Now you know what they're abstracting.

---

## Step 11 — How to Add Your Own Agent

This is the test of whether you understood everything above.

**Goal:** Add a `FactCheckerAgent` that cross-checks the analysis for hallucinations.

### 1. Create the file

```python
# backend/agents/fact_checker.py

from agents.base import BaseAgent
from agents.registry import register_agent
from core.llm import llm

@register_agent("fact_checker")          # ← registers itself
class FactCheckerAgent(BaseAgent):
    name = "fact_checker"

    async def run(self, task: dict) -> dict:
        analysis = task["analysis"]
        pages    = task.get("pages", [])

        await self.emit("thinking", "Cross-checking analysis against sources...")

        verdict = await llm.chat(
            messages=[
                {"role": "system", "content": "You are a fact-checker. Identify claims in the analysis that are NOT supported by the provided sources."},
                {"role": "user",   "content": f"Analysis:\n{analysis}\n\nSources:\n{self._format(pages)}"},
            ],
            temperature=0.1,    # very low — we want deterministic fact-checking
        )

        await self.emit("completed", "Fact-check complete", {"issues_found": "see verdict"})
        return {"verdict": verdict}

    def _format(self, pages):
        return "\n---\n".join(p["content"][:2000] for p in pages)
```

### 2. Import it in main.py

```python
# main.py — add one line in the imports section
import agents.fact_checker   # noqa
```

### 3. Add it to the orchestrator pipeline

```python
# orchestrator.py — after the analyzer step, before the writer step

fact_checker = FactCheckerAgent(self.wf)         # ← same event bus
fact_output  = await fact_checker.run({
    "analysis": analysis,
    "pages": pages,
})
# Pass verdict into the writer so it can include it in the report
write_output = await writer.run({
    "query": query,
    "analysis": analysis,
    "verdict": fact_output.get("verdict"),   # ← add to writer task
    ...
})
```

That's it. **3 changes, all additive.** No existing code modified except the orchestrator pipeline and one import.

---

## Key Patterns to Internalize

### Pattern 1: Data pipeline via dicts
```
OrchestratorAgent.run({"query": q})
  → SearchAgent.run({"queries": [...]})      returns {"results": [...]}
  → ReaderAgent.run({"urls": [...]})         returns {"pages": [...]}
  → AnalyzerAgent.run({"pages": [...]})      returns {"analysis": "..."}
  → WriterAgent.run({"analysis": "..."})     returns {"output_file": "..."}
```
Each agent only knows about its immediate inputs and outputs. No global state.

### Pattern 2: Dependency injection (not singletons)
```python
wf = WorkflowManager(wf_id)      # create once per workflow run
orchestrator = OrchestratorAgent(wf)   # inject
searcher     = SearchAgent(wf)         # inject — same wf
```
Every agent shares the same WorkflowManager → all events go to the same DB row + WebSocket.

### Pattern 3: Emit before and after every meaningful action
```python
await self.emit("searching", "Starting search...")   # ← before
results = self._search(query)                         # ← action
await self.emit("completed", f"Found {len(results)}")# ← after
```
This is what makes the live timeline work. Front-load narration, not just completion.

### Pattern 4: Structured output from LLM
```python
# Tell LLM exactly what format to return
"Return exactly 3 queries as a JSON array. No explanation. Example: [\"q1\", \"q2\", \"q3\"]"

# Parse defensively — find the JSON, don't trust the full response
start = resp.find("[")
end   = resp.rfind("]") + 1
result = json.loads(resp[start:end])
```

---

## What Frameworks Add (and What They Cost)

| Feature | Our code | LangChain | CrewAI | n8n |
|---|---|---|---|---|
| Agent contract | `BaseAgent.run()` | `BaseTool` / `AgentExecutor` | `Agent` class | Node |
| Orchestration | `OrchestratorAgent` | `SequentialChain` / `Plan-and-Execute` | `Crew` | Workflow |
| Memory | SQLite `workflow_events` table | `ConversationBufferMemory` | Built-in | Execution log |
| Tool use | Direct method calls | `Tool(func=...)` | `@tool` decorator | Node connections |
| Real-time | Custom WebSocket | ❌ (polling) | ❌ | ✅ (built-in) |
| Debugging | See every line of code | Stack trace through abstractions | Limited | Visual UI |
| Code you own | 100% | ~10% | ~20% | 0% |
| Lines to understand | ~725 | ~80,000 | ~5,000 | 0 (GUI) |

**When to use a framework:** You're prototyping fast and don't care about the internals.
**When to build raw:** You need to debug, optimize, customize, or run in production with confidence.

---

*This guide was written alongside the `research_agents` codebase at `~/dev_test/research_agents`.*
*Last updated: 2026-06-14*
