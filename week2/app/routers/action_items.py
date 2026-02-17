from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException

from .. import db
from ..schemas import (
    ActionItemDetail,
    ActionItemOut,
    ExtractRequest,
    ExtractResponse,
    MarkDoneRequest,
)
from ..services.extract import extract_action_items, extract_action_items_llm

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/action-items", tags=["action-items"])


@router.post("/extract", response_model=ExtractResponse)
def extract(payload: ExtractRequest) -> ExtractResponse:
    """Extract action items from free-form text (heuristic-based)."""
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    try:
        note_id: Optional[int] = None
        if payload.save_note:
            note_id = db.insert_note(text)

        items = extract_action_items(text)
        ids = db.insert_action_items(items, note_id=note_id)
    except Exception as exc:
        logger.exception("Failed to extract action items")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ExtractResponse(
        note_id=note_id,
        items=[ActionItemOut(id=i, text=t) for i, t in zip(ids, items)],
    )


@router.post("/extract-llm", response_model=ExtractResponse)
def extract_llm(payload: ExtractRequest) -> ExtractResponse:
    """Extract action items from free-form text using an LLM (Ollama)."""
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    try:
        note_id: Optional[int] = None
        if payload.save_note:
            note_id = db.insert_note(text)

        items = extract_action_items_llm(text)
        ids = db.insert_action_items(items, note_id=note_id)
    except Exception as exc:
        logger.exception("Failed to extract action items via LLM")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ExtractResponse(
        note_id=note_id,
        items=[ActionItemOut(id=i, text=t) for i, t in zip(ids, items)],
    )


@router.get("", response_model=List[ActionItemDetail])
def list_all(note_id: Optional[int] = None) -> List[ActionItemDetail]:
    """List all action items, optionally filtered by note_id."""
    try:
        rows = db.list_action_items(note_id=note_id)
    except Exception as exc:
        logger.exception("Failed to list action items")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return [
        ActionItemDetail(
            id=r["id"],
            note_id=r["note_id"],
            text=r["text"],
            done=bool(r["done"]),
            created_at=r["created_at"],
        )
        for r in rows
    ]


@router.post("/{action_item_id}/done")
def mark_done(action_item_id: int, payload: MarkDoneRequest) -> dict:
    """Mark an action item as done or undone."""
    try:
        db.mark_action_item_done(action_item_id, payload.done)
    except Exception as exc:
        logger.exception("Failed to mark action item %s", action_item_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"id": action_item_id, "done": payload.done}


