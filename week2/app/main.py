from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .db import init_db
from .routers import action_items, notes

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Application lifecycle
# ---------------------------------------------------------------------------

FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialise resources on startup and clean up on shutdown."""
    logger.info("Initialising database...")
    init_db()
    yield
    # Shutdown cleanup (if needed in the future) goes here


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(title="Action Item Extractor", lifespan=lifespan)

app.include_router(notes.router)
app.include_router(action_items.router)


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    """Serve the frontend single-page application."""
    html_path = FRONTEND_DIR / "index.html"
    return html_path.read_text(encoding="utf-8")


app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")