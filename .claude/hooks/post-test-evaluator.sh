#!/bin/bash

# Post-Test-Evaluator Hook
# This hook runs after test-evaluator completes
# If PASS: proceed to coder-orchestrator
# If FAIL: return to test-creator to strengthen assertions

set -e

# Parse the hook input from stdin
HOOK_INPUT=$(cat)

# Extract session info
SESSION_ID=$(echo "$HOOK_INPUT" | jq -r '.session_id' 2>/dev/null) || { echo "❌ Failed to parse session_id from input" >&2; exit 1; }
CWD=$(echo "$HOOK_INPUT" | jq -r '.cwd' 2>/dev/null) || { echo "❌ Failed to parse cwd from input" >&2; exit 1; }
SUBAGENT_NAME=$(echo "$HOOK_INPUT" | jq -r '.subagent_name // empty' 2>/dev/null) || { echo "❌ Failed to parse subagent_name from input" >&2; exit 1; }
TRANSCRIPT=$(echo "$HOOK_INPUT" | jq -r '.transcript // empty' 2>/dev/null) || TRANSCRIPT=""

# Validate session_id format (alphanumeric, hyphen, underscore only)
if ! [[ "$SESSION_ID" =~ ^[a-zA-Z0-9_-]+$ ]]; then
  echo "❌ Invalid session_id format" >&2
  exit 1
fi

# Validate CWD is not empty
if [ -z "$CWD" ]; then
  echo "❌ CWD is empty" >&2
  exit 1
fi

# Validate CWD does not contain path traversal sequences
if [[ "$CWD" =~ \.\. ]]; then
  echo "❌ Invalid CWD: path traversal detected" >&2
  exit 1
fi

# Log hook execution
echo "🔍 Post-Test-Evaluator Hook: Processing completion" >&2
echo "   Session: $SESSION_ID" >&2
echo "   Subagent: $SUBAGENT_NAME" >&2

# Only trigger if this is test-evaluator
if [ "$SUBAGENT_NAME" != "test-evaluator" ]; then
  echo "   Skipping: Not a test-evaluator completion" >&2
  exit 0
fi

# Check if evaluation passed or failed by looking at transcript
# Look for failure indicators: "FAIL", "weak assertions", "Returning to"
EVALUATION_FAILED=$(echo "$TRANSCRIPT" | grep -iE "evaluation failed|FAIL|weak assertions|returning to.*test-creator" 2>/dev/null | head -1) || EVALUATION_FAILED=""

if [ -n "$EVALUATION_FAILED" ]; then
  echo "   ⚠️ Test evaluation FAILED - weak assertions detected" >&2

  cat <<EOF
{
  "continue": true,
  "systemMessage": "⚠️ Test evaluation FAILED. Tests have weak assertions (boolean-only, single properties). Invoke test-creator agent to strengthen assertions with full response/object comparisons."
}
EOF
  exit 0
fi

# Evaluation passed - proceed to coder-orchestrator
STATE_DIR="$CWD/.claude/.state"
mkdir -p "$STATE_DIR"
echo "$(date -Iseconds)" > "$STATE_DIR/test-evaluation-passed-${SESSION_ID}"

# Output message to be shown in the transcript
cat <<EOF
{
  "continue": true,
  "systemMessage": "✅ Test evaluation PASSED. All tests have strong assertions. Invoke coder-orchestrator agent to begin implementation."
}
EOF

exit 0
