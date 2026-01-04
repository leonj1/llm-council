# Quick Start - Movie Script Integration Test

Get the integration test running in 5 minutes!

## Step 1: Install Test Dependencies (30 seconds)

```bash
cd /home/jose/src/llm-council
pip install -e ".[test]"
```

Expected output:
```
Successfully installed pytest-7.4.0 pytest-asyncio-0.21.0 pytest-timeout-2.2.0
```

## Step 2: Verify Environment (10 seconds)

```bash
# Check .env file has API key
grep OPENROUTER_API_KEY .env

# Should output something like:
# OPENROUTER_API_KEY=your-api-key-here
```

If missing, add it:
```bash
echo "OPENROUTER_API_KEY=your-key-here" >> .env
```

## Step 3: Start Backend Server (15 seconds)

**In Terminal 1:**
```bash
cd /home/jose/src/llm-council
python -m backend.main
```

Expected output:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8004 (Press CTRL+C to quit)
```

Keep this terminal running!

## Step 4: Quick Server Check (5 seconds)

**In Terminal 2:**
```bash
cd /home/jose/src/llm-council
./run_tests.sh quick
```

Expected output:
```
✓ Backend server is running
test_server_is_running PASSED
```

## Step 5: Run Full Integration Test (10-15 minutes)

```bash
./run_tests.sh full
```

**What to expect:**
- Test will take 10-15 minutes
- You'll see streaming event logs
- Test makes real API calls (costs ~$0.10-$0.50)
- Final output shows detailed validation results

**Success looks like:**
```
============================================================
TEST PASSED - ALL VALIDATIONS SUCCESSFUL
============================================================
Conversation ID: abc123...
Total events: 47
Stage 1 scripts: 4
Stage 2 rankings: 4
Stage 3 winner: google/gemini-3-pro-preview
Stage 4 dialogue: 6 messages
Final script: 15234 characters, 2458 words
============================================================
```

## Troubleshooting

### Problem: "Cannot connect to server"
**Solution:**
```bash
# Make sure backend is running in Terminal 1
python -m backend.main
```

### Problem: "ModuleNotFoundError: No module named 'pytest'"
**Solution:**
```bash
pip install -e ".[test]"
```

### Problem: "OPENROUTER_API_KEY not found"
**Solution:**
```bash
echo "OPENROUTER_API_KEY=your-actual-key" >> .env
```

### Problem: Test times out
**Solution:**
- Check internet connection
- Verify OpenRouter API status
- Increase timeout in pytest.ini if needed

## Alternative: Direct Pytest

Instead of `./run_tests.sh`, you can use pytest directly:

```bash
# Quick check
pytest backend/tests/test_movie_script_integration.py::test_server_is_running -v

# Full test with verbose output
pytest backend/tests/test_movie_script_integration.py::test_movie_script_workflow_end_to_end -v -s
```

## What Gets Tested?

1. **Stage 1**: Multiple models generate movie scripts
2. **Stage 2**: Models peer review and rank scripts
3. **Stage 3**: Best script is selected
4. **Stage 4**: Top 2 models collaborate to refine the script

The test validates:
- All events are received in correct order
- Data structures are correct
- Script content meets quality standards
- Runtime validation works
- Final script contains required elements

## Next Steps

- Review detailed output in terminal
- Check `backend/tests/README.md` for more options
- Read `TESTING.md` for comprehensive documentation
- Review `TEST_SUMMARY.md` for technical details

## Time Breakdown

| Step | Time |
|------|------|
| Install dependencies | 30s |
| Verify environment | 10s |
| Start backend | 15s |
| Quick check | 5s |
| **Full test** | **10-15 min** |
| **Total** | **~15 min** |

## Cost Estimate

- Models queried: 4 (GPT-5.1, Gemini 3 Pro, Claude Opus 4.5, Grok 4)
- Total API calls: 15-20+
- Estimated cost: $0.10-$0.50 per run
- Varies by model pricing and token usage

## Files Created

```
backend/tests/
├── test_movie_script_integration.py  # Main test file (431 lines)
├── conftest.py                       # Pytest fixtures
├── __init__.py                       # Package marker
├── README.md                         # Detailed docs
├── TEST_SUMMARY.md                   # Technical summary
├── PRE_TEST_CHECKLIST.md            # Pre-flight checklist
└── QUICKSTART.md                    # This file

Project root:
├── pytest.ini        # Pytest config
├── run_tests.sh      # Test runner script
└── TESTING.md        # Comprehensive guide
```

## Success Criteria

✅ Server running on port 8004
✅ pytest collecting 2 tests
✅ Quick check passes
✅ Full test completes without errors
✅ All validations pass
✅ Final script generated

---

**Ready?** → `./run_tests.sh full` 🚀
