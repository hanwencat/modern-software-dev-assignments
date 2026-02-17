import json
import os
from unittest.mock import MagicMock, patch

import pytest

from ..app.services.extract import extract_action_items, extract_action_items_llm


# ---------------------------------------------------------------------------
# Existing test for heuristic-based extraction
# ---------------------------------------------------------------------------


def test_extract_bullets_and_checkboxes():
    text = """
    Notes from meeting:
    - [ ] Set up database
    * implement API extract endpoint
    1. Write tests
    Some narrative sentence.
    """.strip()

    items = extract_action_items(text)
    assert "Set up database" in items
    assert "implement API extract endpoint" in items
    assert "Write tests" in items


# ---------------------------------------------------------------------------
# Helper for LLM tests: build a fake ollama chat() response
# ---------------------------------------------------------------------------


def _mock_chat_response(items: list[str]) -> MagicMock:
    """Create a MagicMock that mimics the ollama chat() return value."""
    response = MagicMock()
    response.message.content = json.dumps({"items": items})
    return response


# ---------------------------------------------------------------------------
# Unit tests for extract_action_items_llm()  (TODO 2)
# ---------------------------------------------------------------------------


@patch("week2.app.services.extract.chat")
def test_llm_bullet_list(mock_chat):
    """LLM extraction correctly parses bullet-list action items."""
    mock_chat.return_value = _mock_chat_response([
        "Set up database",
        "Implement API endpoint",
        "Write tests",
    ])

    text = "- [ ] Set up database\n- Implement API endpoint\n1. Write tests"
    items = extract_action_items_llm(text)

    assert items == ["Set up database", "Implement API endpoint", "Write tests"]
    mock_chat.assert_called_once()


@patch("week2.app.services.extract.chat")
def test_llm_keyword_prefixes(mock_chat):
    """LLM extraction handles TODO:/Action:/Next: prefixed lines."""
    mock_chat.return_value = _mock_chat_response([
        "Write integration tests",
        "Review PR #42",
        "Schedule follow-up meeting",
    ])

    text = (
        "TODO: Write integration tests\n"
        "Action: Review PR #42\n"
        "Next: Schedule follow-up meeting"
    )
    items = extract_action_items_llm(text)

    assert items == [
        "Write integration tests",
        "Review PR #42",
        "Schedule follow-up meeting",
    ]
    mock_chat.assert_called_once()


@patch("week2.app.services.extract.chat")
def test_llm_empty_input(mock_chat):
    """Empty or whitespace-only input returns [] without calling the LLM."""
    assert extract_action_items_llm("") == []
    assert extract_action_items_llm("   ") == []
    assert extract_action_items_llm("\n\n") == []

    # chat() should never have been called — we short-circuit on empty input
    mock_chat.assert_not_called()


@patch("week2.app.services.extract.chat")
def test_llm_no_action_items(mock_chat):
    """Narrative text with no action items returns an empty list."""
    mock_chat.return_value = _mock_chat_response([])

    text = "The weather was nice today. We had coffee after the meeting."
    items = extract_action_items_llm(text)

    assert items == []
    mock_chat.assert_called_once()


@patch("week2.app.services.extract.chat")
def test_llm_mixed_format(mock_chat):
    """LLM extraction handles a mix of formats in one block of notes."""
    mock_chat.return_value = _mock_chat_response([
        "Set up database schema",
        "Implement JWT validation",
        "Deploy staging environment",
        "Write integration tests",
    ])

    text = (
        "Meeting notes:\n"
        "John will set up database schema by Friday.\n"
        "- [ ] Implement JWT validation\n"
        "* Deploy staging environment\n"
        "TODO: Write integration tests\n"
        "We had a great lunch."
    )
    items = extract_action_items_llm(text)

    assert len(items) == 4
    assert "Set up database schema" in items
    assert "Implement JWT validation" in items
    mock_chat.assert_called_once()


@patch("week2.app.services.extract.chat")
def test_llm_invalid_response(mock_chat):
    """If the LLM returns unparseable JSON, a validation error is raised."""
    bad_response = MagicMock()
    bad_response.message.content = "this is not valid json"
    mock_chat.return_value = bad_response

    with pytest.raises(Exception):
        extract_action_items_llm("some notes")
