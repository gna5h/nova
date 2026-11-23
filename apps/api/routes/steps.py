from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from core.registry import registry

router = APIRouter()


@router.get("/steps")
async def list_steps() -> dict[str, list[Any]]:
    return {"steps": registry.list()}
