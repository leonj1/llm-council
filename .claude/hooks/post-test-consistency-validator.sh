#!/bin/bash

# Post-Test-Consistency-Validator Hook
# This hook runs after test-consistency-validator completes
# It triggers the test-evaluator agent to assess assertion quality

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
echo "🔍 Post-Test-Consistency-Validator Hook: Processing completion" >&2
echo "   Session: $SESSION_ID" >&2
echo "   Subagent: $SUBAGENT_NAME" >&2

# Only trigger if this is test-consistency-validator
if [ "$SUBAGENT_NAME" != "test-consistency-validator" ]; then
  echo "   Skipping: Not a test-consistency-validator completion" >&2
  exit 0
fi

# Check if validation passed or failed by looking at transcript
VALIDATION_FAILED=$(echo "$TRANSCRIPT" | grep -i "validation failed\|FAIL\|inconsistencies found" 2>/dev/null | head -1) || VALIDATION_FAILED=""

if [ -n "$VALIDATION_FAILED" ]; then
  echo "   ⚠️ Test consistency validation FAILED - returning to test-creator" >&2

  cat <<EOF
{
  "continue": true,
  "systemMessage": "⚠️ Test consistency validation FAILED. Tests have naming inconsistencies. Invoke test-creator agent to fix the tests before proceeding."
}
EOF
  exit 0
fi

# Validation passed - proceed to test-evaluator
STATE_DIR="$CWD/.claude/.state"
mkdir -p "$STATE_DIR"
echo "$(date -Iseconds)" > "$STATE_DIR/test-consistency-validated-${SESSION_ID}"

# Output message to be shown in the transcript
cat <<EOF
{
  "continue": true,
  "systemMessage": "✅ Test consistency validation PASSED. Invoke test-evaluator agent to assess assertion quality before proceeding to implementation."
}
EOF

exit 0
