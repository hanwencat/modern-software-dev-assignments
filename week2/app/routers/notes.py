from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from typing import List

from .. import db
from ..schemas import CreateNoteRequest, NoteResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("", response_model=List[NoteResponse])
def list_all_notes() -> List[NoteResponse]:
    """Retrieve all notes, ordered by most recent first."""
    try:
        rows = db.list_notes()
    except Exception as exc:
        logger.exception("Failed to list notes")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return [
        NoteResponse(id=r["id"], content=r["content"], created_at=r["created_at"])
        for r in rows
    ]


@router.post("", response_model=NoteResponse)
def create_note(payload: CreateNoteRequest) -> NoteResponse:
    """Create a new note."""
    content = payload.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="content is required")

    try:
        note_id = db.insert_note(content)
        note = db.get_note(note_id)
    except Exception as exc:
        logger.exception("Failed to create note")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if note is None:
        raise HTTPException(status_code=500, detail="failed to retrieve created note")

    return NoteResponse(
        id=note["id"],
        content=note["content"],
        created_at=note["created_at"],
    )


@router.get("/{note_id}", response_model=NoteResponse)
def get_single_note(note_id: int) -> NoteResponse:
    """Get a single note by ID."""
    try:
        row = db.get_note(note_id)
    except Exception as exc:
        logger.exception("Failed to get note %s", note_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if row is None:
        raise HTTPException(status_code=404, detail="note not found")

    return NoteResponse(
        id=row["id"],
        content=row["content"],
        created_at=row["created_at"],
    )


