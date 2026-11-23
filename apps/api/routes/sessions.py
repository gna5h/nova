from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, NoReturn

import pandas as pd
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from core.steps.io.load import LoadParams, LoadStep
from core.steps.profile.summary import SummaryParams, SummaryStep
from session import add_step_to_history, add_version, create_session, get_session

MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "10"))
_ALLOWED_EXTS = {"csv", "xlsx"}

router = APIRouter()


def raise_api_error(status: int, code: str, message: str, details: Any = None) -> NoReturn:
    raise HTTPException(
        status_code=status,
        detail={"error": {"code": code, "message": message, "details": details}},
    )


class VersionMeta(BaseModel):
    index: int
    row_count: int
    column_count: int


class StepRunMeta(BaseModel):
    step_id: str
    params: dict[str, Any]
    input_version: int
    output_version: int
    ran_at: str


class SessionStateResponse(BaseModel):
    id: str
    created_at: str
    expires_at: str
    current_version: int | None
    versions: list[VersionMeta]
    history: list[StepRunMeta]


class CreateSessionResponse(SessionStateResponse):
    profile: dict[str, Any]


def _session_to_state(session: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": session["id"],
        "created_at": session["created_at"],
        "expires_at": session["expires_at"],
        "current_version": session["current_version"],
        "versions": [
            VersionMeta(
                index=v["index"],
                row_count=v["row_count"],
                column_count=v["column_count"],
            )
            for v in session["versions"]
        ],
        "history": [
            StepRunMeta(
                step_id=h["step_id"],
                params=h.get("params", {}),
                input_version=h["input_version"],
                output_version=h["output_version"],
                ran_at=h["ran_at"],
            )
            for h in session["history"]
        ],
    }


@router.post("/sessions", status_code=201, response_model=CreateSessionResponse)
async def create_new_session(
    file: UploadFile | None = File(None),
    sample_name: str | None = Form(None),
) -> CreateSessionResponse:
    # Validate: exactly one source provided
    if (file is None) == (sample_name is None):
        raise_api_error(422, "invalid_request", "Provide exactly one of: file or sample_name")

    staged_path: Path | None = None

    try:
        if file is not None:
            content = await file.read()
            if len(content) > MAX_UPLOAD_MB * 1024 * 1024:
                raise_api_error(413, "file_too_large", f"File exceeds {MAX_UPLOAD_MB} MB limit")
            original_filename = file.filename or "upload"
            ext = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else ""
            if ext not in _ALLOWED_EXTS:
                raise_api_error(422, "invalid_file_type", f"Only .csv and .xlsx are supported, got .{ext}")

            tmp_dir = Path(tempfile.mkdtemp())
            staged_path = tmp_dir / original_filename
            staged_path.write_bytes(content)
        else:
            # sample_name provided
            samples_dir = Path(__file__).parents[3] / "samples"
            # Try .csv first, then .xlsx
            for ext in ("csv", "xlsx"):
                candidate = samples_dir / f"{sample_name}.{ext}"
                if candidate.exists():
                    staged_path = candidate
                    original_filename = candidate.name
                    break
            if staged_path is None:
                raise_api_error(404, "sample_not_found", f"Sample '{sample_name}' not found")

        session = create_session()
        session_id: str = session["id"]
        now = datetime.now(timezone.utc).isoformat()

        load_result = LoadStep().run(
            pd.DataFrame(),
            LoadParams(file_path=str(staged_path), original_filename=original_filename),
        )

        v0 = add_version(session_id, load_result.data)

        add_step_to_history(session_id, {
            "step_id": "io.load",
            "params": {"file_path": str(staged_path), "original_filename": original_filename},
            "input_version": -1,
            "output_version": v0,
            "ran_at": now,
        })

        profile_result = SummaryStep().run(load_result.data, SummaryParams())

        add_step_to_history(session_id, {
            "step_id": "profile.summary",
            "params": {},
            "input_version": v0,
            "output_version": v0,
            "ran_at": now,
        })

        profile_dict = profile_result.model_dump(exclude={"data"})
        state = _session_to_state(get_session(session_id))  # type: ignore[arg-type]
        state["profile"] = profile_dict

        return CreateSessionResponse(**state)

    finally:
        # Delete staged upload (not sample files)
        if file is not None and staged_path is not None and staged_path.exists():
            staged_path.unlink(missing_ok=True)


@router.get("/sessions/{session_id}", response_model=SessionStateResponse)
async def get_session_state(session_id: str) -> SessionStateResponse:
    session = get_session(session_id)
    if session is None:
        raise_api_error(404, "session_not_found", f"Session '{session_id}' not found")
    state = _session_to_state(session)
    return SessionStateResponse(**state)
