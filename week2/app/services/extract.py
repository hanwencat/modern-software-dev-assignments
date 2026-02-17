from __future__ import annotations

import os
import re
from typing import List

from ollama import chat
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Ollama model used for LLM-based extraction (overridable via env var)
LLM_MODEL = os.getenv("OLLAMA_MODEL", "qwen3-coder:30b")

# System prompt that instructs the LLM to extract action items
LLM_SYSTEM_PROMPT = (
    "You are an action item extractor. "
    "Given free-form text such as meeting notes, extract every actionable task or to-do item. "
    "Return the result as JSON with a single key 'items' containing a list of strings. "
    "Each string should be a concise, standalone action item. "
    "If there are no action items, return an empty list."
)


# Pydantic model that defines the structured output schema for the LLM
class ActionItems(BaseModel):
    """Schema for LLM structured output: a list of action item strings."""
    items: List[str]


# ---------------------------------------------------------------------------
# Heuristic-based extraction (original implementation)
# ---------------------------------------------------------------------------

BULLET_PREFIX_PATTERN = re.compile(r"^\s*([-*•]|\d+\.)\s+")
KEYWORD_PREFIXES = (
    "todo:",
    "action:",
    "next:",
)


def _is_action_line(line: str) -> bool:
    stripped = line.strip().lower()
    if not stripped:
        return False
    if BULLET_PREFIX_PATTERN.match(stripped):
        return True
    if any(stripped.startswith(prefix) for prefix in KEYWORD_PREFIXES):
        return True
    if "[ ]" in stripped or "[todo]" in stripped:
        return True
    return False


def extract_action_items(text: str) -> List[str]:
    lines = text.splitlines()
    extracted: List[str] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        if _is_action_line(line):
            cleaned = BULLET_PREFIX_PATTERN.sub("", line)
            cleaned = cleaned.strip()
            # Trim common checkbox markers
            cleaned = cleaned.removeprefix("[ ]").strip()
            cleaned = cleaned.removeprefix("[todo]").strip()
            extracted.append(cleaned)
    # Fallback: if nothing matched, heuristically split into sentences and pick imperative-like ones
    if not extracted:
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        for sentence in sentences:
            s = sentence.strip()
            if not s:
                continue
            if _looks_imperative(s):
                extracted.append(s)
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: List[str] = []
    for item in extracted:
        lowered = item.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        unique.append(item)
    return unique


def _looks_imperative(sentence: str) -> bool:
    words = re.findall(r"[A-Za-z']+", sentence)
    if not words:
        return False
    first = words[0]
    # Crude heuristic: treat these as imperative starters
    imperative_starters = {
        "add",
        "create",
        "implement",
        "fix",
        "update",
        "write",
        "check",
        "verify",
        "refactor",
        "document",
        "design",
        "investigate",
    }
    return first.lower() in imperative_starters


# ---------------------------------------------------------------------------
# LLM-powered extraction (TODO 1)
# ---------------------------------------------------------------------------

def extract_action_items_llm(text: str) -> List[str]:
    """Extract action items from free-form text using an Ollama LLM.

    Uses structured output (JSON schema) to guarantee the model returns
    a well-formed list of strings.  Falls back to raising a RuntimeError
    if the LLM call or response parsing fails.
    """
    # Short-circuit on empty / whitespace-only input
    if not text.strip():
        return []

    response = chat(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": LLM_SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        format=ActionItems.model_json_schema(),
    )

    # Parse the structured JSON response via Pydantic for validation
    result = ActionItems.model_validate_json(response.message.content)
    return result.items
