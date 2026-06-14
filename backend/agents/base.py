from abc import ABC, abstractmethod
from core.workflow import WorkflowManager


class BaseAgent(ABC):
    """
    All agents subclass this. Override `run(task)` with your logic.
    Use `self.emit(event_type, message, data)` to broadcast real-time updates.
    """

    name: str = "base"

    def __init__(self, wf: WorkflowManager):
        self.wf = wf

    async def emit(self, event_type: str, message: str, data: dict | None = None):
        await self.wf.emit(self.name, event_type, message, data)

    @abstractmethod
    async def run(self, task: dict) -> dict:
        """Execute the agent task. Return a dict with results."""
        ...
