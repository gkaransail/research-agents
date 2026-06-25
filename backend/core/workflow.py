import json
import uuid
from datetime import datetime, timezone
from fastapi import WebSocket
from loguru import logger

from core import database as db


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, workflow_id: str, ws: WebSocket):
        await ws.accept()
        self._connections.setdefault(workflow_id, []).append(ws)
        logger.info(f"WS connected | workflow={workflow_id}")

    def disconnect(self, workflow_id: str, ws: WebSocket):
        conns = self._connections.get(workflow_id, [])
        if ws in conns:
            conns.remove(ws)
        logger.info(f"WS disconnected | workflow={workflow_id}")

    async def broadcast(self, workflow_id: str, message: dict):
        conns = self._connections.get(workflow_id, [])
        dead = []
        for ws in conns:
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                dead.append(ws)
        for ws in dead:
            conns.remove(ws)


manager = ConnectionManager()


class WorkflowManager:
    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id

    async def emit(self, agent_name: str, event_type: str, message: str, data: dict | None = None):
        ev_id = str(uuid.uuid4())
        ts = _now()
        await db.insert_event(ev_id, self.workflow_id, agent_name, event_type, message, data, ts)
        payload = {
            "type": "event",
            "event": {
                "id": ev_id,
                "workflow_id": self.workflow_id,
                "agent_name": agent_name,
                "event_type": event_type,
                "message": message,
                "data": data,
                "timestamp": ts,
            },
        }
        await manager.broadcast(self.workflow_id, payload)
        logger.info(f"[{agent_name}] {event_type}: {message}")

    async def set_status(self, status: str, output_file: str | None = None):
        now = _now()
        await db.update_workflow_status(self.workflow_id, status, now, output_file)
        await manager.broadcast(
            self.workflow_id,
            {"type": "status", "status": status, "output_file": output_file},
        )


async def create_workflow(query: str, workflow_type: str = "research") -> str:
    wf_id = str(uuid.uuid4())
    now = _now()
    await db.create_workflow(wf_id, query, now, workflow_type)
    return wf_id
