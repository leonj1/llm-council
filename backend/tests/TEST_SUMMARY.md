# Movie Script Integration Test - Summary

## Overview

A comprehensive end-to-end integration test for the LLM Council movie script workflow.

**File**: `test_movie_script_integration.py`
**Lines of Code**: 431
**Duration**: 10-15 minutes
**Type**: Integration (requires running server and API keys)

## Test Functions

### 1. `test_server_is_running()`
- **Purpose**: Quick connectivity check
- **Duration**: < 10 seconds
- **Markers**: `@pytest.mark.asyncio`, `@pytest.mark.integration`
- **Validates**: Server is accessible at http://localhost:8004

### 2. `test_movie_script_workflow_end_to_end()`
- **Purpose**: Complete workflow validation
- **Duration**: 10-15 minutes
- **Markers**: `@pytest.mark.asyncio`, `@pytest.mark.slow`, `@pytest.mark.integration`
- **API Calls**: 15-20+ calls to OpenRouter
- **Cost**: ~$0.10-$0.50 per run

## Test Coverage

### Stage 1: Script Generation ✓
- Scripts from multiple models
- Proper data structure (model, response)
- Non-trivial content (> 100 chars)
- Contains screenplay elements (TITLE, LOGLINE, GENRE, OUTLINE, SCENE)

### Stage 2: Peer Review ✓
- Rankings from all models
- Label-to-model mapping
- Aggregate rankings calculation
- Parsed ranking validation

### Stage 3: Best Script Selection ✓
- Winning model selection
- Winning script identification
- Collaborators designation (≥ 2)
- Selection rationale

### Stage 4: Collaborative Dialogue ✓
- Correct number of dialogue turns (num_turns × 2)
- Proper message structure
- Role alternation (author/collaborator)
- Final refined script generation
- Runtime validation

### Additional Validations ✓
- Event sequence (correct order)
- SSE event parsing
- Word count and runtime estimation
- Thematic elements from prompt
- Screenplay formatting (INT./EXT./SCENE)

## Validation Details

### Event Types Validated
- `stage1_start`, `stage1_complete`
- `validation_start`, `validation_result`, `validation_complete`
- `stage2_start`, `stage2_complete`
- `stage3_start`, `stage3_complete`
- `stage4_start`, `stage4_turn`, `stage4_complete`
- `title_complete`, `complete`, `error`

### Data Structure Checks

**Stage 1 Response:**
```json
[
  {
    "model": "openai/gpt-5.1",
    "response": "**TITLE:** ...",
    "runtime_validation": {...}
  }
]
```

**Stage 2 Response:**
```json
{
  "data": [...],
  "metadata": {
    "label_to_model": {"Script A": "openai/gpt-5.1"},
    "aggregate_rankings": [
      {
        "model": "openai/gpt-5.1",
        "average_rank": 1.5,
        "rankings_count": 4
      }
    ]
  }
}
```

**Stage 3 Response:**
```json
{
  "winning_model": "openai/gpt-5.1",
  "winning_script": "**TITLE:** ...",
  "collaborators": ["openai/gpt-5.1", "google/gemini-3-pro-preview"],
  "selection_rationale": "..."
}
```

**Stage 4 Response:**
```json
{
  "dialogue_history": [
    {
      "turn": 1,
      "model": "openai/gpt-5.1",
      "role": "author",
      "message": "..."
    }
  ],
  "refined_script": "**TITLE:** ...",
  "collaborators": [...],
  "num_turns": 3,
  "runtime_validation": {...}
}
```

## Assertions

### Total Assertions: 100+

Key assertion categories:
1. **Completion checks** (5) - All stages complete
2. **Data presence** (20) - Required fields exist
3. **Data types** (30) - Correct types (list, dict, str, etc.)
4. **Content validation** (25) - Non-empty, proper length
5. **Structure validation** (15) - Proper nesting, expected keys
6. **Sequence validation** (5) - Correct event order
7. **Quality checks** (10) - Script elements, formatting
8. **Thematic validation** (2) - Prompt requirements met

## Test Flow

```
1. Create Conversation
   ↓
2. Send Movie Script Request (SSE streaming)
   ↓
3. Parse Events:
   - stage1_start
   - stage1_complete → Validate
   - validation_result (per model)
   - validation_complete
   - stage2_start
   - stage2_complete → Validate
   - stage3_start
   - stage3_complete → Validate
   - stage4_start
   - stage4_turn (multiple)
   - validation_start
   - validation_result (final)
   - validation_complete
   - stage4_complete → Validate
   - title_complete
   - complete
   ↓
4. Run All Validations
   ↓
5. Assert Success
```

## Configuration

### Test Parameters
```python
BASE_URL = "http://localhost:8004"
TIMEOUT = 900.0  # 15 minutes
PROMPT = "Create a movie script that combines John Wick and Terminator."
MOVIE_LENGTH = 90  # minutes
NUM_TURNS = 3  # dialogue turns
```

### Expected Models
- openai/gpt-5.1
- google/gemini-3-pro-preview
- anthropic/claude-opus-4.5
- x-ai/grok-4

(Actual models from `backend/config.py`)

## Sample Output

```
=== Creating new conversation ===
Created conversation: abc123...

=== Sending movie script request ===
Prompt: Create a movie script that combines John Wick and Terminator.
Movie length: 90 minutes
Dialogue turns: 3

=== Processing streaming events ===
[EVENT] stage1_start
[EVENT] stage1_complete
  Stage 1: Received 4 scripts
[EVENT] validation_result
  Validation: openai/gpt-5.1 - compliant
...
[EVENT] complete
  Workflow complete!

============================================================
VALIDATING RESULTS
============================================================

--- Stage 1 Validation ---
Stage 1: 4 scripts validated

--- Stage 2 Validation ---
Stage 2: 4 rankings validated
  Label to model mappings: 4
  Aggregate rankings: 4

--- Stage 3 Validation ---
Stage 3: Winner is google/gemini-3-pro-preview
  Collaborators: 2

--- Stage 4 Validation ---
Stage 4: Dialogue complete with 6 messages
  Final script length: 15234 characters
  Script elements found: ['TITLE', 'LOGLINE', 'GENRE', 'OUTLINE', 'RUNTIME']

--- Runtime Validation ---
Validation events: 5
  Compliant scripts: 3/5

--- Final Script Quality Checks ---
  Word count: 2458
  Estimated runtime: 16.4 minutes (target: 90)
  References: John Wick=True, Terminator=True

============================================================
TEST PASSED - ALL VALIDATIONS SUCCESSFUL
============================================================
```

## Error Handling

The test handles various error scenarios:
- Server not running → Clear error message
- API failures → Continues with successful responses
- Missing data → Specific assertion failures
- Timeout → Configurable timeout (15 min default)
- Parse errors → Logged warnings, test continues

## Dependencies

### Python Packages
- `pytest>=7.4.0` - Test framework
- `pytest-asyncio>=0.21.0` - Async test support
- `pytest-timeout>=2.2.0` - Timeout support
- `httpx>=0.27.0` - HTTP client (already in main deps)

### External Services
- OpenRouter API (requires valid API key)
- Backend server running on port 8004

## Fixtures (from conftest.py)

- `base_url`: Backend URL
- `movie_script_prompt`: Default prompt
- `movie_length`: Default length (90 min)
- `num_turns`: Default turns (3)

## Markers

- `@pytest.mark.asyncio` - Async test
- `@pytest.mark.slow` - Takes 10+ minutes
- `@pytest.mark.integration` - Requires external services

## Running the Test

```bash
# Quick way
./run_tests.sh full

# Direct pytest
pytest backend/tests/test_movie_script_integration.py::test_movie_script_workflow_end_to_end -v

# With output
pytest backend/tests/test_movie_script_integration.py::test_movie_script_workflow_end_to_end -v -s

# Custom timeout
pytest backend/tests/test_movie_script_integration.py -v --timeout=1200
```

## Success Criteria

✅ All stages complete without errors
✅ All data structures present and valid
✅ Event sequence is correct
✅ Final script contains required elements
✅ Dialogue history has expected turns
✅ Runtime validation performed
✅ Thematic elements from prompt present
✅ Proper screenplay formatting

## Known Limitations

1. **Non-deterministic**: LLM responses vary, so exact content differs between runs
2. **API dependent**: Requires external API availability
3. **Cost incurring**: Each run costs money
4. **Time consuming**: Takes 10-15 minutes
5. **Network dependent**: Requires stable internet connection

## Future Enhancements

- [ ] Add mock tests (no API calls)
- [ ] Add unit tests for parsing functions
- [ ] Add performance benchmarks
- [ ] Add error scenario tests
- [ ] Add tests for different movie lengths
- [ ] Add tests for different num_turns
- [ ] Add validation for edge cases
- [ ] Add tests for concurrent requests
