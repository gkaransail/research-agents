from abc import ABC, abstractmethod
from core.workflow import WorkflowManager


class BaseAgent(ABC):
    name: str = "base"

    def __init__(self, wf: WorkflowManager):
        self.wf = wf

    async def emit(self, event_type: str, message: str, data: dict | None = None):
        await self.wf.emit(self.name, event_type, message, data)

    @abstractmethod
    async def run(self, task: dict) -> dict: ...
