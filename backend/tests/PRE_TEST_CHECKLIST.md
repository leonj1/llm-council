# Pre-Test Checklist

Before running the movie script integration test, ensure all prerequisites are met.

## Environment Setup

- [ ] Python 3.10+ installed
- [ ] Project directory: `/home/jose/src/llm-council`
- [ ] Virtual environment activated (if using one)

## Dependencies

- [ ] Main dependencies installed: `pip install -e .`
- [ ] Test dependencies installed: `pip install -e ".[test]"` or `pip install pytest pytest-asyncio pytest-timeout`
- [ ] Verify pytest is available: `pytest --version`

## Configuration

- [ ] `.env` file exists in project root
- [ ] `OPENROUTER_API_KEY` is set in `.env`
- [ ] API key is valid and has sufficient credits
- [ ] Network connection is stable

## Backend Server

- [ ] Backend server is running: `python -m backend.main`
- [ ] Server is accessible at `http://localhost:8004`
- [ ] Port 8004 is not blocked by firewall
- [ ] Quick check passes: `./run_tests.sh quick` OR `curl http://localhost:8004/api/conversations`

## Council Models

Verify these models are configured in `backend/config.py`:

- [ ] `openai/gpt-5.1` (or current OpenAI model)
- [ ] `google/gemini-3-pro-preview` (or current Gemini model)
- [ ] `anthropic/claude-opus-4.5` (or current Claude model)
- [ ] `x-ai/grok-4` (or current Grok model)

## Test Files

- [ ] Test file exists: `backend/tests/test_movie_script_integration.py`
- [ ] Pytest can collect tests: `pytest backend/tests/ --collect-only`
- [ ] No syntax errors in test file

## Expectations

- [ ] Understand test will take 10-15 minutes
- [ ] Understand test will make 15-20+ API calls
- [ ] Understand test will incur API costs (~$0.10-$0.50)
- [ ] Prepared to wait for completion

## Optional (Recommended)

- [ ] Review test parameters in `test_movie_script_integration.py`:
  - `BASE_URL`
  - `TIMEOUT`
  - `PROMPT`
  - `MOVIE_LENGTH`
  - `NUM_TURNS`
- [ ] Check available disk space for logs
- [ ] Close unnecessary applications
- [ ] Keep terminal window open

## Run Test

Once all items are checked:

```bash
# Recommended: Use helper script
./run_tests.sh full

# Alternative: Direct pytest
pytest backend/tests/test_movie_script_integration.py::test_movie_script_workflow_end_to_end -v
```

## During Test Execution

- [ ] Monitor progress via event logs
- [ ] Watch for any error messages
- [ ] Note which stage is currently executing
- [ ] Be patient - each stage takes time

## After Test Completion

- [ ] Review test output summary
- [ ] Check if all assertions passed
- [ ] Review final script quality
- [ ] Check conversation in backend storage (optional)
- [ ] Note any warnings or unexpected behavior

## Troubleshooting

If any checklist item fails:

**Backend not running:**
```bash
python -m backend.main
```

**Dependencies missing:**
```bash
pip install -e ".[test]"
```

**API key issues:**
```bash
# Check .env file
cat .env | grep OPENROUTER_API_KEY

# Verify it's not empty
```

**Port already in use:**
```bash
# Find process on port 8004
lsof -i :8004

# Kill process if needed
kill -9 <PID>
```

**Test collection fails:**
```bash
# Check Python version
python --version  # or python3 --version

# Verify pytest
pytest --version

# Check for syntax errors
python -m py_compile backend/tests/test_movie_script_integration.py
```

## Quick Reference

```bash
# Essential commands
cd /home/jose/src/llm-council
source .venv/bin/activate  # if using venv
python -m backend.main     # in one terminal
./run_tests.sh quick       # in another terminal
./run_tests.sh full        # run the actual test
```

## Notes

- The test is idempotent - safe to run multiple times
- Each run creates a new conversation
- Test does not interfere with existing data
- Can be stopped with Ctrl+C (though partial results will be lost)

---

**Ready to run?** ✓ All items checked? → `./run_tests.sh full`
