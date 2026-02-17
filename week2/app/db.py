"""SQLite database layer for the Action Item Extractor.

All database access is funnelled through this module so that the rest of
the application stays independent of the storage backend.
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "app.db"


# ---------------------------------------------------------------------------
# Connection helpers
# ---------------------------------------------------------------------------


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    """Return a new SQLite connection with Row factory enabled."""
    _ensure_data_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# Schema initialisation
# ---------------------------------------------------------------------------


def init_db() -> None:
    """Create tables if they do not already exist."""
    _ensure_data_dir()
    try:
        with get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    created_at TEXT DEFAULT (datetime('now'))
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS action_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    note_id INTEGER,
                    text TEXT NOT NULL,
                    done INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (note_id) REFERENCES notes(id)
                );
                """
            )
            conn.commit()
    except sqlite3.Error:
        logger.exception("Failed to initialise database")
        raise


# ---------------------------------------------------------------------------
# Notes CRUD
# ---------------------------------------------------------------------------


def insert_note(content: str) -> int:
    """Insert a note and return its new ID."""
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO notes (content) VALUES (?)", (content,)
            )
            conn.commit()
            return int(cursor.lastrowid)  # type: ignore[arg-type]
    except sqlite3.Error:
        logger.exception("Failed to insert note")
        raise


def list_notes() -> list[dict[str, Any]]:
    """Return all notes ordered by most recent first."""
    try:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT id, content, created_at FROM notes ORDER BY id DESC"
            ).fetchall()
            return [dict(r) for r in rows]
    except sqlite3.Error:
        logger.exception("Failed to list notes")
        raise


def get_note(note_id: int) -> Optional[dict[str, Any]]:
    """Return a single note by ID, or None if not found."""
    try:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT id, content, created_at FROM notes WHERE id = ?",
                (note_id,),
            ).fetchone()
            return dict(row) if row else None
    except sqlite3.Error:
        logger.exception("Failed to get note %s", note_id)
        raise


# ---------------------------------------------------------------------------
# Action Items CRUD
# ---------------------------------------------------------------------------


def insert_action_items(
    items: list[str], note_id: Optional[int] = None
) -> list[int]:
    """Insert multiple action items and return their new IDs."""
    try:
        with get_connection() as conn:
            ids: list[int] = []
            for item in items:
                cursor = conn.execute(
                    "INSERT INTO action_items (note_id, text) VALUES (?, ?)",
                    (note_id, item),
                )
                ids.append(int(cursor.lastrowid))  # type: ignore[arg-type]
            conn.commit()
            return ids
    except sqlite3.Error:
        logger.exception("Failed to insert action items")
        raise


def list_action_items(
    note_id: Optional[int] = None,
) -> list[dict[str, Any]]:
    """Return action items, optionally filtered by note_id."""
    try:
        with get_connection() as conn:
            if note_id is None:
                rows = conn.execute(
                    "SELECT id, note_id, text, done, created_at "
                    "FROM action_items ORDER BY id DESC"
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id, note_id, text, done, created_at "
                    "FROM action_items WHERE note_id = ? ORDER BY id DESC",
                    (note_id,),
                ).fetchall()
            return [dict(r) for r in rows]
    except sqlite3.Error:
        logger.exception("Failed to list action items")
        raise


def mark_action_item_done(action_item_id: int, done: bool) -> None:
    """Update the done status of an action item."""
    try:
        with get_connection() as conn:
            conn.execute(
                "UPDATE action_items SET done = ? WHERE id = ?",
                (1 if done else 0, action_item_id),
            )
            conn.commit()
    except sqlite3.Error:
        logger.exception("Failed to mark action item %s", action_item_id)
        raise


