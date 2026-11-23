from __future__ import annotations

from typing import Any, Literal, Protocol

import pandas as pd
from pydantic import BaseModel


class StepParams(BaseModel):
    """Base class for step parameters. Each Step subclasses this."""


class ResultTable(BaseModel):
    title: str
    columns: list[str]
    rows: list[list[Any]]


class ChartSpec(BaseModel):
    type: str
    title: str
    spec: dict[str, Any]


class OutputFile(BaseModel):
    id: str
    filename: str
    mime_type: str


class ChangeEntry(BaseModel):
    row: int
    column: str
    old_value: Any
    new_value: Any
    reason: str


class StepResult(BaseModel):
    data: Any | None = None  # pd.DataFrame — excluded from serialisation
    tables: list[ResultTable] = []
    charts: list[ChartSpec] = []
    files: list[OutputFile] = []
    change_log: list[ChangeEntry] = []
    facts: dict[str, Any] = {}
    warnings: list[str] = []

    model_config = {"arbitrary_types_allowed": True}


class Step(Protocol):
    id: str
    category: Literal["io", "profile", "clean", "aggregate", "stats", "export"]
    title: str
    description: str
    Params: type[StepParams]

    def run(self, df: pd.DataFrame, params: StepParams) -> StepResult: ...
