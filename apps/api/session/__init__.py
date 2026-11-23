from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

_sessions: dict[str, dict[str, Any]] = {}

SESSION_TTL_MINUTES = 60


def create_session() -> dict[str, Any]:
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    session: dict[str, Any] = {
        "id": session_id,
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(minutes=SESSION_TTL_MINUTES)).isoformat(),
        "versions": [],
        "history": [],
        "current_version": None,
    }
    _sessions[session_id] = session
    return session


def get_session(session_id: str) -> dict[str, Any] | None:
    return _sessions.get(session_id)
