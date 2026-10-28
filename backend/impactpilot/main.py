"""ImpactPilot v2 FastAPI application."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_ROOT / ".env")

from impactpilot.api import compendium, evidence, initiatives, llm  # noqa: E402
from impactpilot.jobs.refresh_guidance import refresh_in_background_if_stale  # noqa: E402
from impactpilot.persistence.db import init_db  # noqa: E402


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    refresh_in_background_if_stale()
    yield


app = FastAPI(title="ImpactPilot", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("IMPACTPILOT_CORS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(initiatives.router)
app.include_router(llm.router)
app.include_router(evidence.router)
app.include_router(compendium.router)


def create_app() -> FastAPI:
    return app
