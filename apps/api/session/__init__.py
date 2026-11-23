from __future__ import annotations

import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd

_sessions: dict[str, dict[str, Any]] = {}

SESSION_TTL_MINUTES = 60


def create_session() -> dict[str, Any]:
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    data_dir = Path(tempfile.mkdtemp())
    session: dict[str, Any] = {
        "id": session_id,
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(minutes=SESSION_TTL_MINUTES)).isoformat(),
        "versions": [],
        "history": [],
        "current_version": None,
        "data_dir": str(data_dir),
    }
    _sessions[session_id] = session
    return session


def get_session(session_id: str) -> dict[str, Any] | None:
    return _sessions.get(session_id)


def add_version(session_id: str, df: pd.DataFrame) -> int:
    session = _sessions[session_id]
    index = len(session["versions"])
    data_dir = Path(session["data_dir"])
    parquet_path = data_dir / f"v{index}.parquet"
    df.to_parquet(str(parquet_path), index=False)
    session["versions"].append({
        "index": index,
        "parquet_path": str(parquet_path),
        "row_count": len(df),
        "column_count": len(df.columns),
    })
    session["current_version"] = index
    return index


def get_version_df(session_id: str, version: int) -> pd.DataFrame:
    session = _sessions[session_id]
    parquet_path = session["versions"][version]["parquet_path"]
    return pd.read_parquet(parquet_path)


def add_step_to_history(session_id: str, meta: dict[str, Any]) -> None:
    session = _sessions[session_id]
    session["history"].append(meta)
