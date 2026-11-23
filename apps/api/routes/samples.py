from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

SAMPLE_METADATA: dict[str, str] = {
    "churn_sample": "Bank churn demo dataset (20 rows, 12 columns)",
}


class SampleMeta(BaseModel):
    name: str
    filename: str
    description: str


@router.get("/samples")
async def list_samples() -> dict[str, list[SampleMeta]]:
    samples_dir = Path(__file__).parents[3] / "samples"
    results: list[SampleMeta] = []

    if samples_dir.exists():
        for f in sorted(samples_dir.iterdir()):
            if f.suffix.lower() in (".csv", ".xlsx"):
                name = f.stem
                description = SAMPLE_METADATA.get(name, f"{name} dataset")
                results.append(SampleMeta(name=name, filename=f.name, description=description))

    return {"samples": results}
