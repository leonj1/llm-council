# LLM Council Integration Tests

This directory contains integration tests for the LLM Council backend, specifically for the movie script workflow.

## Overview

The integration tests validate the complete end-to-end workflow including:
- **Stage 1**: Multiple LLMs generate movie scripts
- **Stage 2**: Peer review and ranking of scripts
- **Stage 3**: Selection of the best script
- **Stage 4**: Collaborative dialogue and refinement

## Prerequisites

1. **Backend Server Running**: The backend must be running on port 8004
2. **API Keys**: You must have a valid `OPENROUTER_API_KEY` configured in your `.env` file
3. **Test Dependencies**: Install test dependencies (see below)

## Installation

Install the project with test dependencies:

```bash
# From project root
pip install -e ".[test]"
```

Or install test dependencies manually:

```bash
pip install pytest pytest-asyncio pytest-timeout
```

## Running the Tests

### Start the Backend Server

First, make sure the backend server is running:

```bash
# From project root
python -m backend.main
```

The server should be accessible at `http://localhost:8004`.

### Run All Tests

```bash
# From project root
pytest backend/tests/
```

### Run Only Integration Tests

```bash
pytest backend/tests/ -m integration
```

### Run Excluding Slow Tests

```bash
pytest backend/tests/ -m "not slow"
```

### Run Specific Test

```bash
pytest backend/tests/test_movie_script_integration.py::test_movie_script_workflow_end_to_end -v
```

### Quick Server Check

Before running the full integration test, verify the server is accessible:

```bash
pytest backend/tests/test_movie_script_integration.py::test_server_is_running -v
```

## Test Configuration

### Timeout

The integration test has a timeout of **15 minutes** (900 seconds) to allow for:
- Multiple LLM API calls
- Stage 1: Parallel script generation from all council models
- Stage 2: Parallel peer review
- Stage 3: Best script selection
- Stage 4: Multi-turn collaborative dialogue (3 turns by default)
- Runtime validation and refinement

### Test Parameters

You can modify the test parameters in `test_movie_script_integration.py`:

```python
BASE_URL = "http://localhost:8004"  # Backend server URL
TIMEOUT = 900.0                      # 15 minutes
PROMPT = "Create a movie script that combines John Wick and Terminator."
MOVIE_LENGTH = 90                    # 90 minutes
NUM_TURNS = 3                        # Dialogue turns in Stage 4
```

## What the Test Validates

### Stage 1 Validation
- Scripts are received from multiple models
- Each script has `model` and `response` fields
- Scripts contain expected elements (TITLE, LOGLINE, GENRE, OUTLINE, SCENE)
- Script content is non-trivial (> 100 characters)

### Stage 2 Validation
- Rankings are received from all models
- `label_to_model` mapping is present and valid
- `aggregate_rankings` are calculated correctly
- Each ranking has `parsed_ranking` list

### Stage 3 Validation
- Winning model is selected
- Winning script is identified
- At least 2 collaborators are designated for Stage 4
- Selection rationale is provided

### Stage 4 Validation
- Dialogue history contains correct number of turns (num_turns × 2)
- Each turn has proper structure (turn, model, role, message)
- Roles alternate between "author" and "collaborator"
- Refined script is generated
- Refined script contains expected screenplay elements
- Runtime validation is performed

### Event Sequence Validation
- All stage completion events are received
- Events occur in correct order (stage1 → stage2 → stage3 → stage4 → complete)
- No errors are reported

### Final Script Quality
- Word count is calculated
- Estimated runtime is computed
- Thematic elements from the prompt are present
- Proper screenplay formatting (INT./EXT./SCENE headings)

## Markers

The tests use pytest markers for categorization:

- `@pytest.mark.slow` - Tests that take a long time (10+ minutes)
- `@pytest.mark.integration` - Integration tests requiring running server
- `@pytest.mark.asyncio` - Async tests using pytest-asyncio

## Troubleshooting

### Server Connection Error

```
Cannot connect to server at http://localhost:8004
```

**Solution**: Make sure the backend server is running:
```bash
python -m backend.main
```

### API Key Error

If you get errors about API keys or authentication:

**Solution**: Ensure your `.env` file has a valid `OPENROUTER_API_KEY`:
```bash
OPENROUTER_API_KEY=your-key-here
```

### Timeout Error

If the test times out:

**Solution**:
1. Check your internet connection
2. Increase the timeout in `pytest.ini` or the test file
3. Reduce `NUM_TURNS` to speed up Stage 4

### Validation Failures

If specific validations fail, the test will show which assertion failed. Common issues:

- **Missing script elements**: Model didn't follow the expected format
- **Event sequence wrong**: Backend logic changed
- **Word count off**: Runtime validation may need adjustment

## Test Output

The test provides detailed output including:

```
=== Creating new conversation ===
Created conversation: 123e4567-e89b-12d3-a456-426614174000

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

=== VALIDATING RESULTS ===
--- Stage 1 Validation ---
Stage 1: 4 scripts validated
...

TEST PASSED - ALL VALIDATIONS SUCCESSFUL
Total events: 47
Final script: 15234 characters, 2458 words
```

## CI/CD Integration

To integrate with CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run Integration Tests
  run: |
    python -m backend.main &
    sleep 5  # Wait for server to start
    pytest backend/tests/ -m integration -v
  env:
    OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
```

## Contributing

When adding new tests:

1. Use appropriate markers (`@pytest.mark.integration`, `@pytest.mark.slow`)
2. Use async/await for async operations
3. Provide detailed assertion messages
4. Document expected behavior
5. Include print statements for debugging

## Notes

- **Real API Calls**: This test makes actual calls to LLM providers via OpenRouter
- **Cost**: Each test run will incur API costs based on your usage
- **Time**: Expect 10-15 minutes per full test run
- **Non-Deterministic**: LLM responses vary, so exact content will differ between runs
