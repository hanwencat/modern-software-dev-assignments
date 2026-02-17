"""Pydantic request/response schemas for the Action Item Extractor API.

Centralises all API contracts so that routers stay thin and the FastAPI
auto-generated docs (/docs) accurately reflect the expected payloads.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class ExtractRequest(BaseModel):
    """Body for POST /action-items/extract."""
    text: str
    save_note: bool = False


class CreateNoteRequest(BaseModel):
    """Body for POST /notes."""
    content: str


class MarkDoneRequest(BaseModel):
    """Body for POST /action-items/{id}/done."""
    done: bool = True


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class ActionItemOut(BaseModel):
    """A single action item returned after extraction."""
    id: int
    text: str


class ActionItemDetail(BaseModel):
    """Full action item record (used in list endpoints)."""
    id: int
    note_id: Optional[int] = None
    text: str
    done: bool
    created_at: str


class ExtractResponse(BaseModel):
    """Response for POST /action-items/extract."""
    note_id: Optional[int] = None
    items: List[ActionItemOut]


class NoteResponse(BaseModel):
    """Response representing a single note."""
    id: int
    content: str
    created_at: str
