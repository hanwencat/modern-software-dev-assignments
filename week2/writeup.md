# Week 2 Write-up
Tip: To preview this markdown file
- On Mac, press `Command (⌘) + Shift + V`
- On Windows/Linux, press `Ctrl + Shift + V`

## INSTRUCTIONS

Fill out all of the `TODO`s in this file.

## SUBMISSION DETAILS

Name: **TODO** \
SUNet ID: **TODO** \
Citations: **TODO**

This assignment took me about **TODO** hours to do. 


## YOUR RESPONSES
For each exercise, please include what prompts you used to generate the answer, in addition to the location of the generated response. Make sure to clearly add comments in your code documenting which parts are generated.

### Exercise 1: Scaffold a New Feature
Prompt: 
```
Implement an LLM-powered alternative extract_action_items_llm() in extract.py that uses
Ollama to perform action item extraction. Use Pydantic to define a structured output schema
(ActionItems with a list of strings), and pass it to Ollama's format parameter to constrain
the model output to valid JSON. Use the model qwen3-coder:30b (overridable via the
OLLAMA_MODEL environment variable). Empty input should short-circuit and return an empty list
without calling the LLM.
``` 

Generated Code Snippets:
```
week2/app/services/extract.py:
  - Lines 1-33: New imports (pydantic BaseModel), LLM_MODEL constant, LLM_SYSTEM_PROMPT,
    ActionItems Pydantic model
  - Lines 119-145: New extract_action_items_llm() function
```

### Exercise 2: Add Unit Tests
Prompt: 
```
Write unit tests for extract_action_items_llm() in test_extract.py. Use @patch to mock the
ollama chat() call so tests don't require a running Ollama service. Cover these scenarios:
bullet list input, keyword-prefix input (TODO:/Action:/Next:), empty/whitespace input
(verify chat is not called), narrative text with no action items, mixed format input, and
invalid JSON response from the LLM (should raise an exception).
``` 

Generated Code Snippets:
```
week2/tests/test_extract.py:
  - Lines 1-7: Updated imports (json, unittest.mock, extract_action_items_llm)
  - Lines 35-39: _mock_chat_response() helper function
  - Lines 47-60: test_llm_bullet_list()
  - Lines 63-84: test_llm_keyword_prefixes()
  - Lines 87-95: test_llm_empty_input()
  - Lines 98-107: test_llm_no_action_items()
  - Lines 110-133: test_llm_mixed_format()
  - Lines 136-144: test_llm_invalid_response()
```

### Exercise 3: Refactor Existing Code for Clarity
Prompt: 
```
Refactor the backend code focusing on four areas: (1) Replace all Dict[str, Any] with
Pydantic models for well-defined API contracts — create a new schemas.py with request and
response models. (2) Clean up the database layer — return dict instead of sqlite3.Row, add
try-except for sqlite3.Error with logging. (3) Move init_db() from module-level call to
FastAPI lifespan context manager. (4) Add error handling in routers — wrap database
operations in try-except, log errors, and return appropriate HTTP error responses.
``` 

Generated/Modified Code Snippets:
```
week2/app/schemas.py (NEW FILE):
  - Lines 1-65: ExtractRequest, CreateNoteRequest, MarkDoneRequest, ActionItemOut,
    ActionItemDetail, ExtractResponse, NoteResponse

week2/app/routers/action_items.py:
  - Lines 1-80: Rewrote entirely — imported Pydantic schemas, changed endpoint signatures
    to use typed models, added response_model, wrapped DB ops in try-except with logging

week2/app/routers/notes.py:
  - Lines 1-58: Rewrote entirely — same Pydantic migration, added defensive None check
    after insert_note + get_note

week2/app/main.py:
  - Lines 1-50: Rewrote entirely — init_db() moved into async lifespan context manager,
    extracted FRONTEND_DIR constant, removed unused imports

week2/app/db.py:
  - Lines 1-170: Rewrote entirely — return types changed from sqlite3.Row to dict[str, Any],
    all functions wrapped in try-except catching sqlite3.Error with logger.exception(),
    ensure_data_directory_exists renamed to private _ensure_data_dir, added module docstring
```


### Exercise 4: Use Agentic Mode to Automate a Small Task
Prompt: 
```
(1) Add a new POST /action-items/extract-llm endpoint in action_items.py that calls
extract_action_items_llm(). (2) Add a new GET /notes endpoint in notes.py that returns all
saved notes. (3) Update the frontend index.html: add an "Extract LLM" button that triggers
the new LLM endpoint, and a "List Notes" button that fetches and displays all notes. Refactor
the JS to extract a shared doExtract() function to avoid duplicating the extraction logic.
``` 

Generated Code Snippets:
```
week2/app/routers/action_items.py:
  - Line 16: Added import of extract_action_items_llm
  - Lines 47-68: New extract_llm() endpoint

week2/app/routers/notes.py:
  - Line 7: Added List import
  - Lines 17-29: New list_all_notes() endpoint

week2/frontend/index.html:
  - Lines 15-18: New CSS styles for note cards (.notes-section, .note-card)
  - Lines 27-28: New "Extract LLM" and "List Notes" buttons
  - Lines 29-33: New notes list section (hidden by default)
  - Lines 35-83: Refactored JS — shared doExtract() function, Extract LLM click handler,
    List Notes click handler with note card rendering
```


### Exercise 5: Generate a README from the Codebase
Prompt: 
```
Analyze the current codebase and generate a well-structured week2/README.md. Include: project
overview (what the app does, two extraction strategies), project directory structure, setup
and run instructions (conda, poetry, Ollama model pull, uvicorn), all API endpoints with
methods/paths/descriptions and request/response examples, instructions for running the test
suite, and a configuration table for environment variables.
``` 

Generated Code Snippets:
```
week2/README.md (NEW FILE):
  - Lines 1-145: Complete README with project overview, structure, setup instructions,
    API endpoint documentation, test instructions, and configuration reference
```


## SUBMISSION INSTRUCTIONS
1. Hit a `Command (⌘) + F` (or `Ctrl + F`) to find any remaining `TODO`s in this file. If no results are found, congratulations – you've completed all required fields. 
2. Make sure you have all changes pushed to your remote repository for grading.
3. Submit via Gradescope. 