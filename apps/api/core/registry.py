from __future__ import annotations

from typing import Any

_registry: dict[str, Any] = {}


def register_step(cls: Any) -> Any:
    """Decorator that registers a Step class in the global registry."""
    _registry[cls.id] = cls
    return cls


class _Registry:
    def list(self) -> list[dict[str, Any]]:
        return [
            {
                "id": step_cls.id,
                "category": step_cls.category,
                "title": step_cls.title,
                "description": step_cls.description,
                "params_schema": step_cls.Params.model_json_schema(),
            }
            for step_cls in _registry.values()
        ]

    def get(self, step_id: str) -> Any:
        if step_id not in _registry:
            raise KeyError(f"Step '{step_id}' not found in registry")
        return _registry[step_id]


registry = _Registry()
