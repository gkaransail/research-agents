from typing import Type, TYPE_CHECKING

if TYPE_CHECKING:
    from agents.base import BaseAgent

_REGISTRY: dict[str, Type["BaseAgent"]] = {}


def register_agent(name: str):
    def decorator(cls: Type["BaseAgent"]) -> Type["BaseAgent"]:
        _REGISTRY[name] = cls
        return cls
    return decorator


def get_agent(name: str) -> Type["BaseAgent"]:
    if name not in _REGISTRY:
        raise KeyError(f"Agent '{name}' not registered. Available: {list(_REGISTRY.keys())}")
    return _REGISTRY[name]


def list_agents() -> list[str]:
    return list(_REGISTRY.keys())
