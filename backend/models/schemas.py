from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class EventType(str, Enum):
    STARTED = "started"
    THINKING = "thinking"
    SEARCHING = "searching"
    READING = "reading"
    ANALYZING = "analyzing"
    WRITING = "writing"
    COMPLETED = "completed"
    ERROR = "error"
    INFO = "info"
    PLANNING = "planning"


class WorkflowCreate(BaseModel):
    query: str
    depth: int = 3  # 1=fast (3 sources), 2=normal (5), 3=deep (8)


class DDWorkflowCreate(BaseModel):
    asset_name: str
    asset_type: str = "real estate"
    asset_location: str
    asset_description: str = ""
    depth: int = 2


class TokenizeRequest(BaseModel):
    private_key: str
    rpc_url: str = "http://127.0.0.1:8545"


class WorkflowEventOut(BaseModel):
    id: str
    workflow_id: str
    agent_name: str
    event_type: str
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: str


class WorkflowOut(BaseModel):
    id: str
    query: str
    status: WorkflowStatus
    created_at: str
    updated_at: str
    output_file: Optional[str] = None
    type: str = "research"
    events: List[WorkflowEventOut] = []


class WorkflowListItem(BaseModel):
    id: str
    query: str
    status: WorkflowStatus
    created_at: str
    updated_at: str
    output_file: Optional[str] = None
    type: str = "research"
