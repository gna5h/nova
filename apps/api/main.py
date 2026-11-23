from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import step modules to trigger @register_step decorators before any request
import core.steps.io  # noqa: F401
import core.steps.profile  # noqa: F401

from routes.health import router as health_router
from routes.samples import router as samples_router
from routes.sessions import router as sessions_router
from routes.steps import router as steps_router

app = FastAPI(
    title="Nova API",
    description="Data Analyst AI Dev Assistant",
    version="0.1.0",
)

allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
allowed_origins = [o.strip() for o in allowed_origins_raw.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(steps_router)
app.include_router(sessions_router)
app.include_router(samples_router)
