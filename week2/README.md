# Action Item Extractor

A FastAPI + SQLite web application that converts free-form notes into structured, actionable to-do items. It supports both **heuristic-based** and **LLM-powered** extraction.

## Project Overview

Paste meeting notes, brainstorming sessions, or any free-form text into the web interface and the application will extract actionable tasks. Two extraction strategies are available:

- **Heuristic extraction** — uses pattern matching (bullet lists, keyword prefixes like `TODO:`, checkbox markers) and imperative-sentence detection.
- **LLM extraction** — sends the text to a local [Ollama](https://ollama.com/) model that understands natural language and returns structured JSON action items.

Extracted items are persisted in a SQLite database and can be marked as done via the UI.

## Project Structure

```
week2/
├── app/
│   ├── main.py              # FastAPI app entry point & lifecycle
│   ├── db.py                # SQLite database layer
│   ├── schemas.py           # Pydantic request/response models
│   ├── routers/
│   │   ├── action_items.py  # /action-items endpoints
│   │   └── notes.py         # /notes endpoints
│   └── services/
│       └── extract.py       # Heuristic & LLM extraction logic
├── frontend/
│   └── index.html           # Single-page HTML/JS frontend
├── data/
│   └── app.db               # SQLite database (auto-created)
└── tests/
    └── test_extract.py      # Unit tests for extraction functions
```

## Setup

### Prerequisites

- Python 3.10+
- [Conda](https://docs.conda.io/) (with the `cs146s` environment)
- [Poetry](https://python-poetry.org/) for dependency management
- [Ollama](https://ollama.com/) installed and running (for LLM extraction)

### Installation

1. Activate the conda environment:

   ```bash
   conda activate cs146s
   ```

2. Install dependencies:

   ```bash
   poetry install
   ```

3. Pull an Ollama model (if you haven't already):

   ```bash
   ollama run qwen3-coder:30b
   ```

   You can use a different model by setting the `OLLAMA_MODEL` environment variable.

### Running the Server

From the project root:

```bash
poetry run uvicorn week2.app.main:app --reload
```

Then open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.

## API Endpoints

### Action Items

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/action-items/extract` | Extract action items using heuristic rules |
| `POST` | `/action-items/extract-llm` | Extract action items using an LLM (Ollama) |
| `GET` | `/action-items` | List all action items (optional `?note_id=` filter) |
| `POST` | `/action-items/{id}/done` | Mark an action item as done/undone |

**Extract request body:**

```json
{
  "text": "Your notes here...",
  "save_note": true
}
```

**Extract response:**

```json
{
  "note_id": 1,
  "items": [
    { "id": 1, "text": "Set up database" },
    { "id": 2, "text": "Write tests" }
  ]
}
```

### Notes

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/notes` | List all saved notes |
| `POST` | `/notes` | Create a new note |
| `GET` | `/notes/{id}` | Get a single note by ID |

### Interactive API Docs

FastAPI auto-generates interactive documentation at:

- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## Running Tests

```bash
poetry run pytest week2/tests/test_extract.py -v
```

The test suite includes:

- **Heuristic extraction tests** — verifies bullet list, checkbox, and numbered list parsing
- **LLM extraction tests** — uses mocked Ollama responses to verify:
  - Bullet list input parsing
  - Keyword-prefix input parsing (`TODO:`, `Action:`, `Next:`)
  - Empty/whitespace input short-circuits without calling the LLM
  - Narrative text with no action items returns an empty list
  - Mixed-format input handling
  - Invalid LLM response raises an exception

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `OLLAMA_MODEL` | `qwen3-coder:30b` | Ollama model used for LLM extraction |
