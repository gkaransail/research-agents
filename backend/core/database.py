import aiosqlite
import json
from core.config import settings

DB = settings.DATABASE_PATH

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS workflows (
    id TEXT PRIMARY KEY,
    query TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    output_file TEXT
);

CREATE TABLE IF NOT EXISTS workflow_events (
    id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    event_type TEXT NOT NULL,
    message TEXT NOT NULL,
    data TEXT,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (workflow_id) REFERENCES workflows(id)
);

CREATE INDEX IF NOT EXISTS idx_events_workflow ON workflow_events(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflows_created ON workflows(created_at DESC);
"""


async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.executescript(CREATE_SQL)
        await db.commit()


async def create_workflow(wf_id: str, query: str, now: str):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT INTO workflows (id, query, status, created_at, updated_at) VALUES (?, ?, 'pending', ?, ?)",
            (wf_id, query, now, now),
        )
        await db.commit()


async def update_workflow_status(wf_id: str, status: str, now: str, output_file: str = None):
    async with aiosqlite.connect(DB) as db:
        if output_file:
            await db.execute(
                "UPDATE workflows SET status=?, updated_at=?, output_file=? WHERE id=?",
                (status, now, output_file, wf_id),
            )
        else:
            await db.execute(
                "UPDATE workflows SET status=?, updated_at=? WHERE id=?",
                (status, now, wf_id),
            )
        await db.commit()


async def insert_event(ev_id: str, wf_id: str, agent: str, etype: str, msg: str, data: dict, ts: str):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT INTO workflow_events (id, workflow_id, agent_name, event_type, message, data, timestamp) VALUES (?,?,?,?,?,?,?)",
            (ev_id, wf_id, agent, etype, msg, json.dumps(data) if data else None, ts),
        )
        await db.commit()


async def get_workflow(wf_id: str) -> dict | None:
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM workflows WHERE id=?", (wf_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def get_workflow_events(wf_id: str) -> list[dict]:
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM workflow_events WHERE workflow_id=? ORDER BY timestamp ASC", (wf_id,)
        ) as cur:
            rows = await cur.fetchall()
            result = []
            for r in rows:
                d = dict(r)
                if d["data"]:
                    d["data"] = json.loads(d["data"])
                result.append(d)
            return result


async def list_workflows() -> list[dict]:
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM workflows ORDER BY created_at DESC LIMIT 100") as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]
