import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from loguru import logger

from core import database as db
from core.config import settings
from core.workflow import manager, WorkflowManager, create_workflow
from models.schemas import WorkflowCreate, WorkflowOut, WorkflowListItem, WorkflowEventOut

# Import agents to register them
import agents.searcher  # noqa
import agents.reader    # noqa
import agents.analyzer  # noqa
import agents.writer    # noqa
import agents.orchestrator  # noqa
from agents.registry import list_agents
from agents.orchestrator import OrchestratorAgent


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_db()
    logger.info(f"DB ready | agents={list_agents()}")
    yield


app = FastAPI(title="Research Agents API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Workflows ─────────────────────────────────────────────────────────────────

@app.post("/api/workflows", response_model=WorkflowListItem, status_code=201)
async def start_research(body: WorkflowCreate, background_tasks: BackgroundTasks):
    wf_id = await create_workflow(body.query)
    background_tasks.add_task(_run_research, wf_id, body.query, body.depth)
    row = await db.get_workflow(wf_id)
    return WorkflowListItem(**row)


@app.get("/api/workflows", response_model=list[WorkflowListItem])
async def list_workflows():
    rows = await db.list_workflows()
    return [WorkflowListItem(**r) for r in rows]


@app.get("/api/workflows/{wf_id}", response_model=WorkflowOut)
async def get_workflow(wf_id: str):
    row = await db.get_workflow(wf_id)
    if not row:
        raise HTTPException(404, "Workflow not found")
    events = await db.get_workflow_events(wf_id)
    return WorkflowOut(**row, events=[WorkflowEventOut(**e) for e in events])


@app.delete("/api/workflows/{wf_id}", status_code=204)
async def delete_workflow(wf_id: str):
    row = await db.get_workflow(wf_id)
    if not row:
        raise HTTPException(404, "Workflow not found")
    async with __import__("aiosqlite").connect(settings.DATABASE_PATH) as conn:
        await conn.execute("DELETE FROM workflow_events WHERE workflow_id=?", (wf_id,))
        await conn.execute("DELETE FROM workflows WHERE id=?", (wf_id,))
        await conn.commit()


# ── Outputs ───────────────────────────────────────────────────────────────────

@app.get("/api/outputs")
async def list_outputs():
    out_dir = Path(settings.OUTPUT_DIR)
    if not out_dir.exists():
        return []
    files = sorted(out_dir.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)
    return [{"filename": f.name, "size": f.stat().st_size, "path": str(f)} for f in files]


@app.get("/api/outputs/{filename}")
async def get_output(filename: str):
    path = Path(settings.OUTPUT_DIR) / filename
    if not path.exists() or not path.suffix == ".md":
        raise HTTPException(404, "File not found")
    return PlainTextResponse(path.read_text(encoding="utf-8"))


# ── Agents info ───────────────────────────────────────────────────────────────

@app.get("/api/agents")
async def get_agents():
    return {"agents": list_agents()}


# ── WebSocket ─────────────────────────────────────────────────────────────────

@app.websocket("/ws/{wf_id}")
async def websocket_endpoint(websocket: WebSocket, wf_id: str):
    await manager.connect(wf_id, websocket)
    # Send existing events on connect (catch-up for late subscribers)
    events = await db.get_workflow_events(wf_id)
    for ev in events:
        await websocket.send_text(
            __import__("json").dumps({"type": "event", "event": ev})
        )
    row = await db.get_workflow(wf_id)
    if row:
        await websocket.send_text(
            __import__("json").dumps({"type": "status", "status": row["status"], "output_file": row.get("output_file")})
        )
    try:
        while True:
            await websocket.receive_text()  # keep alive
    except WebSocketDisconnect:
        manager.disconnect(wf_id, websocket)


# ── Background task ───────────────────────────────────────────────────────────

async def _run_research(wf_id: str, query: str, depth: int):
    wf = WorkflowManager(wf_id)
    await wf.set_status("running")
    try:
        orchestrator = OrchestratorAgent(wf)
        result = await orchestrator.run({"query": query, "depth": depth})
        output_file = result.get("output_file")
        await wf.set_status("completed", output_file)
    except Exception as e:
        logger.exception(f"Workflow {wf_id} failed: {e}")
        await wf.emit("orchestrator", "error", f"Research failed: {str(e)}")
        await wf.set_status("failed")
