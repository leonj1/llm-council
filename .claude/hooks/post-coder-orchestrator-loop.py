#!/usr/bin/env python3
"""
Coder Orchestrator Loop Hook

This hook runs after the coder-orchestrator agent completes and checks if there
are remaining incomplete tasks. If tasks remain, it returns an error to trigger
re-invocation of the coder-orchestrator. If all tasks are complete, it signals
success to proceed to quality gates.

Task sources checked:
- feature_list.md: Looks for "[ ] Incomplete" entries
- architects_digest.md: Looks for "(Pending)" entries

Input format (JSON from stdin):
{
    "session_id": "...",
    "cwd": "...",
    "subagent_name": "coder-orchestrator",
    "subagent_result": "..."
}

Output format:
- If tasks remain: {"error": "..."} with exit code 1
- If complete: {"continue": true, "systemMessage": "..."} with exit code 0
"""
import json
import re
import sys
from pathlib import Path


def count_incomplete_features(cwd: str) -> tuple[int, list[str]]:
    """
    Count incomplete features in feature_list.md.

    Returns:
        Tuple of (count, list of incomplete feature names)
    """
    feature_file = Path(cwd) / "feature_list.md"
    if not feature_file.exists():
        return 0, []

    content = feature_file.read_text()

    # Match "[ ] Incomplete" or just "[ ]" followed by feature text
    # Pattern: - [ ] Incomplete: Feature name OR - [ ] Feature name
    incomplete_pattern = r"^\s*-\s*\[ \]\s*(?:Incomplete:\s*)?(.+)$"
    matches = re.findall(incomplete_pattern, content, re.MULTILINE)

    return len(matches), matches[:5]  # Return first 5 for display


def count_pending_tasks(cwd: str) -> tuple[int, list[str]]:
    """
    Count pending tasks in architects_digest.md.

    Returns:
        Tuple of (count, list of pending task names)
    """
    digest_file = Path(cwd) / "architects_digest.md"
    if not digest_file.exists():
        return 0, []

    content = digest_file.read_text()

    # Match lines containing "(Pending)"
    pending_pattern = r"^.*\(Pending\).*$"
    matches = re.findall(pending_pattern, content, re.MULTILINE)

    # Clean up matches for display
    cleaned = [m.strip()[:60] for m in matches]

    return len(matches), cleaned[:5]  # Return first 5 for display


def main():
    # Parse input from stdin
    try:
        input_data = sys.stdin.read()
        if not input_data or not input_data.strip():
            # No input, allow to continue
            print(json.dumps({
                "continue": True,
                "systemMessage": "No hook input received. Proceeding."
            }))
            sys.exit(0)

        data = json.loads(input_data)
    except json.JSONDecodeError:
        # Invalid JSON, allow to continue
        print(json.dumps({
            "continue": True,
            "systemMessage": "Invalid hook input. Proceeding."
        }))
        sys.exit(0)

    # Extract working directory
    cwd = data.get("cwd", ".")
    subagent_name = data.get("subagent_name", "")

    # Only process for coder-orchestrator
    if subagent_name != "coder-orchestrator":
        print(json.dumps({
            "continue": True,
            "systemMessage": f"Skipping: Not coder-orchestrator (got {subagent_name})"
        }))
        sys.exit(0)

    # Count remaining tasks
    feature_count, feature_names = count_incomplete_features(cwd)
    pending_count, pending_names = count_pending_tasks(cwd)

    total_remaining = feature_count + pending_count

    if total_remaining > 0:
        # Build error message with task details
        error_parts = [
            f"INCOMPLETE TASKS DETECTED: {total_remaining} task(s) remain.",
            "",
            "Re-invoke coder-orchestrator to continue processing tasks.",
        ]

        if feature_count > 0:
            error_parts.append(f"\nIncomplete features ({feature_count}):")
            for name in feature_names:
                error_parts.append(f"  - {name}")
            if feature_count > 5:
                error_parts.append(f"  ... and {feature_count - 5} more")

        if pending_count > 0:
            error_parts.append(f"\nPending tasks ({pending_count}):")
            for name in pending_names:
                error_parts.append(f"  - {name}")
            if pending_count > 5:
                error_parts.append(f"  ... and {pending_count - 5} more")

        error_message = "\n".join(error_parts)

        print(json.dumps({
            "error": error_message
        }))
        sys.exit(1)

    # All tasks complete - proceed to quality gates
    print(json.dumps({
        "continue": True,
        "systemMessage": "All coding tasks complete. Coding standards checker will be invoked next."
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
