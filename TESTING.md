# Testing Guide for LLM Council

This guide explains how to run tests for the LLM Council project, specifically the movie script workflow integration tests.

## Quick Start

```bash
# 1. Start the backend server
python -m backend.main

# 2. In another terminal, run the quick server check
./run_tests.sh quick

# 3. Run the full integration test (takes 10-15 minutes)
./run_tests.sh full
```

## Test Structure

```
backend/tests/
├── __init__.py                          # Package marker
├── conftest.py                          # Pytest configuration and fixtures
├── test_movie_script_integration.py     # Main integration test
└── README.md                            # Detailed test documentation
```

## Prerequisites

### 1. Install Test Dependencies

```bash
# Install project with test dependencies
pip install -e ".[test]"

# Or install manually
pip install pytest pytest-asyncio pytest-timeout
```

### 2. Environment Setup

Ensure you have a `.env` file with your OpenRouter API key:

```bash
OPENROUTER_API_KEY=your-key-here
```

### 3. Start Backend Server

The integration tests require the backend server to be running:

```bash
python -m backend.main
```

The server should be accessible at `http://localhost:8004`.

## Running Tests

### Using the Helper Script (Recommended)

```bash
# Quick server connectivity check (< 1 min)
./run_tests.sh quick

# Full end-to-end movie script test (10-15 min)
./run_tests.sh full

# All integration tests
./run_tests.sh integration

# All slow tests
./run_tests.sh slow

# All tests
./run_tests.sh all
```

### Using Pytest Directly

```bash
# Run all tests
pytest backend/tests/ -v

# Run only integration tests
pytest backend/tests/ -m integration -v

# Run excluding slow tests
pytest backend/tests/ -m "not slow" -v

# Run specific test with verbose output
pytest backend/tests/test_movie_script_integration.py::test_movie_script_workflow_end_to_end -v -s

# Run with custom timeout
pytest backend/tests/ -v --timeout=1200
```

## Test Coverage

### test_server_is_running

**Duration**: < 10 seconds
**Purpose**: Quick sanity check to verify the backend server is accessible
**Markers**: `@pytest.mark.integration`

This test simply makes a GET request to `/api/conversations` to verify connectivity.

### test_movie_script_workflow_end_to_end

**Duration**: 10-15 minutes
**Purpose**: Comprehensive end-to-end validation of the movie script workflow
**Markers**: `@pytest.mark.asyncio`, `@pytest.mark.slow`, `@pytest.mark.integration`

This test validates:

#### Stage 1: Script Generation
- ✓ Scripts received from multiple models
- ✓ Each script has `model` and `response` fields
- ✓ Scripts contain expected elements (TITLE, LOGLINE, GENRE, OUTLINE, SCENE)
- ✓ Scripts are non-trivial (> 100 characters)

#### Stage 2: Peer Review
- ✓ Rankings received from all models
- ✓ `label_to_model` mapping is valid
- ✓ `aggregate_rankings` calculated correctly
- ✓ Each ranking has `parsed_ranking` list

#### Stage 3: Best Script Selection
- ✓ Winning model is selected
- ✓ Winning script is identified
- ✓ At least 2 collaborators designated
- ✓ Selection rationale provided

#### Stage 4: Collaborative Dialogue
- ✓ Dialogue history has correct number of turns
- ✓ Each turn has proper structure
- ✓ Roles alternate (author/collaborator)
- ✓ Refined script generated
- ✓ Script contains screenplay elements
- ✓ Runtime validation performed

#### Event Sequence
- ✓ All stage events received
- ✓ Events in correct order
- ✓ No errors reported

#### Final Script Quality
- ✓ Word count calculated
- ✓ Estimated runtime computed
- ✓ Thematic elements present
- ✓ Proper screenplay formatting

## Test Configuration

### Default Parameters

These can be modified in `test_movie_script_integration.py`:

```python
BASE_URL = "http://localhost:8004"  # Backend server URL
TIMEOUT = 900.0                      # 15 minutes
PROMPT = "Create a movie script that combines John Wick and Terminator."
MOVIE_LENGTH = 90                    # Target runtime in minutes
NUM_TURNS = 3                        # Dialogue turns in Stage 4
```

### Pytest Configuration

The `pytest.ini` file contains global pytest settings:

```ini
[pytest]
markers =
    slow: marks tests as slow (10+ minutes)
    integration: requires running server and API keys
    unit: fast tests with no external dependencies

asyncio_mode = auto
timeout = 1000
```

## Fixtures

Available pytest fixtures (defined in `conftest.py`):

- `base_url`: Returns `"http://localhost:8004"`
- `movie_script_prompt`: Default test prompt
- `movie_length`: Default movie length (90 minutes)
- `num_turns`: Default dialogue turns (3)

Usage:

```python
@pytest.mark.asyncio
async def test_something(base_url, movie_script_prompt):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{base_url}/api/conversations", ...)
```

## Understanding Test Output

The test provides detailed streaming output:

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
[EVENT] validation_result
  Validation: google/gemini-3-pro-preview - too_short
...
[EVENT] stage4_complete
  Stage 4: Final script length 15234 chars
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
  Word count within tolerance range (10125-16875)
  References: John Wick=True, Terminator=True

--- Event Sequence Validation ---
  Events in correct order
  Event sequence: stage1_complete -> stage2_complete -> stage3_complete -> stage4_complete -> complete

============================================================
TEST PASSED - ALL VALIDATIONS SUCCESSFUL
============================================================
Conversation ID: 123e4567-e89b-12d3-a456-426614174000
Total events: 47
Stage 1 scripts: 4
Stage 2 rankings: 4
Stage 3 winner: google/gemini-3-pro-preview
Stage 4 dialogue: 6 messages
Final script: 15234 characters, 2458 words
============================================================
```

## Troubleshooting

### Connection Error

```
Cannot connect to server at http://localhost:8004
```

**Solution**: Start the backend server:
```bash
python -m backend.main
```

### API Key Error

```
Error: API authentication failed
```

**Solution**: Check your `.env` file has a valid `OPENROUTER_API_KEY`.

### Timeout Error

```
pytest.TimeoutExpired: Test exceeded timeout of 900.0 seconds
```

**Solutions**:
1. Check your internet connection
2. Increase timeout in `pytest.ini` or test file
3. Reduce `NUM_TURNS` to speed up Stage 4
4. Check if OpenRouter API is experiencing issues

### Validation Failures

If a specific validation fails, the test output will show which assertion failed:

```
AssertionError: Script 0 missing expected screenplay elements
```

**Common Causes**:
- Model didn't follow expected format
- Backend logic changed
- Prompt needs adjustment

**Debug Steps**:
1. Review the raw output in test logs
2. Check if models are responding correctly
3. Verify backend endpoints haven't changed

### Import Errors

```
ModuleNotFoundError: No module named 'pytest'
```

**Solution**: Install test dependencies:
```bash
pip install -e ".[test]"
```

## CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        pip install -e ".[test]"

    - name: Start backend
      run: |
        python -m backend.main &
        sleep 10
      env:
        OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}

    - name: Run integration tests
      run: |
        pytest backend/tests/ -m integration -v
      env:
        OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
```

## Best Practices

1. **Always run quick check first**: Use `./run_tests.sh quick` to verify server connectivity before running the full test suite

2. **Monitor API costs**: Each full test run makes 15-20+ LLM API calls, which incurs costs

3. **Use verbose mode**: Add `-v` or `-vv` to pytest commands for detailed output

4. **Capture output**: Use `-s` flag to see print statements during test execution

5. **Run tests in isolation**: The integration test is designed to be independent and won't interfere with existing data

6. **Check logs**: Backend logs (if enabled) can help debug failures

## Cost Considerations

Each full integration test run:
- Makes 15-20+ API calls to OpenRouter
- Uses multiple models (GPT-5.1, Gemini 3 Pro, Claude Opus 4.5, Grok 4)
- Generates ~10,000-20,000 tokens across all stages
- Estimated cost: $0.10-$0.50 per run (varies by model pricing)

## Next Steps

- Add unit tests for individual functions
- Add mock tests that don't require API calls
- Add performance benchmarks
- Add regression tests for specific edge cases
- Add tests for error handling scenarios

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [Backend Tests README](backend/tests/README.md)
- Project CLAUDE.md for architecture details
