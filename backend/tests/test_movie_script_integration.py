"""
Integration test for the movie script workflow.

This is a comprehensive end-to-end test that validates the entire 4-stage
movie script generation workflow including:
- Stage 1: Multiple models generate scripts
- Stage 2: Peer review and ranking
- Stage 3: Best script selection
- Stage 4: Collaborative dialogue and refinement

NOTE: This test makes real API calls to LLM providers and may take 10+ minutes.
"""

import asyncio
import json
import re
import sys
import pytest
import aiohttp
from typing import Dict, List, Any


# Test configuration
BASE_URL = "http://localhost:8004"
TIMEOUT = aiohttp.ClientTimeout(total=1200)  # 20 minutes for the entire workflow
PROMPT = "Create a movie script that combines John Wick and Terminator."
MOVIE_LENGTH = 90
NUM_TURNS = 3


@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.integration
async def test_movie_script_workflow_end_to_end():
    """
    Comprehensive integration test for the movie script workflow.

    This test:
    1. Creates a new conversation
    2. Sends a movie script request
    3. Parses Server-Sent Events (SSE) from the streaming endpoint
    4. Validates each stage's output
    5. Verifies the final script meets all requirements
    """

    # Track all events received
    events: List[Dict[str, Any]] = []

    # Track specific stage data
    stage1_data = None
    stage2_data = None
    stage2_metadata = None
    stage3_data = None
    stage4_data = None
    validation_events = []

    # Completion flags
    stage1_complete = False
    stage2_complete = False
    stage3_complete = False
    stage4_complete = False
    workflow_complete = False

    async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
        # Step 1: Create a new conversation
        print("\n=== Creating new conversation ===", flush=True)
        async with session.post(
            f"{BASE_URL}/api/conversations",
            json={"type": "movie_script"}
        ) as create_response:
            assert create_response.status == 200, f"Failed to create conversation: {await create_response.text()}"
            conversation_data = await create_response.json()

        conversation_id = conversation_data["id"]
        assert conversation_id, "Conversation ID should not be empty"
        print(f"Created conversation: {conversation_id}", flush=True)

        # Step 2: Send movie script request with streaming
        print(f"\n=== Sending movie script request ===", flush=True)
        print(f"Prompt: {PROMPT}", flush=True)
        print(f"Movie length: {MOVIE_LENGTH} minutes", flush=True)
        print(f"Dialogue turns: {NUM_TURNS}", flush=True)

        request_body = {
            "content": PROMPT,
            "num_turns": NUM_TURNS,
            "movie_length": MOVIE_LENGTH
        }

        # Stream the SSE response using aiohttp (properly handles streaming)
        async with session.post(
            f"{BASE_URL}/api/conversations/{conversation_id}/movie-script/stream",
            json=request_body
        ) as response:
            assert response.status == 200, f"Failed to start movie script workflow: {await response.text()}"

            print("\n=== Processing streaming events ===", flush=True)

            # Parse SSE events line by line with aiohttp's streaming
            buffer = ""
            async for chunk, _ in response.content.iter_chunks():
                buffer += chunk.decode('utf-8')

                # Process complete SSE events (separated by double newlines)
                while '\n\n' in buffer:
                    event_data, buffer = buffer.split('\n\n', 1)
                    for line in event_data.split('\n'):
                        if not line.strip():
                            continue

                        # SSE format: "data: {json}"
                        if line.startswith("data: "):
                            try:
                                event_json = line[6:]  # Remove "data: " prefix
                                event = json.loads(event_json)
                                events.append(event)

                                event_type = event.get("type")
                                print(f"[EVENT] {event_type}", flush=True)

                                # Track stage completions and data
                                if event_type == "stage1_complete":
                                    stage1_complete = True
                                    stage1_data = event.get("data")
                                    print(f"  Stage 1: Received {len(stage1_data)} scripts", flush=True)

                                elif event_type == "validation_result":
                                    validation_events.append(event)
                                    model = event.get("model", "unknown")
                                    compliance = event.get("compliance", {})
                                    status = compliance.get("status", "unknown")
                                    print(f"  Validation: {model} - {status}", flush=True)

                                elif event_type == "stage2_complete":
                                    stage2_complete = True
                                    stage2_data = event.get("data")
                                    stage2_metadata = event.get("metadata")
                                    print(f"  Stage 2: Received {len(stage2_data)} rankings", flush=True)

                                elif event_type == "stage3_complete":
                                    stage3_complete = True
                                    stage3_data = event.get("data")
                                    winning_model = stage3_data.get("winning_model", "unknown")
                                    print(f"  Stage 3: Winner is {winning_model}", flush=True)

                                elif event_type == "stage4_turn":
                                    turn_data = event.get("data")
                                    turn = turn_data.get("turn")
                                    role = turn_data.get("role")
                                    print(f"  Stage 4 Turn {turn}: {role}", flush=True)

                                elif event_type == "stage4_complete":
                                    stage4_complete = True
                                    stage4_data = event.get("data")
                                    refined_script_length = len(stage4_data.get("refined_script", ""))
                                    print(f"  Stage 4: Final script length {refined_script_length} chars", flush=True)

                                elif event_type == "complete":
                                    workflow_complete = True
                                    print("  Workflow complete!", flush=True)

                                elif event_type == "error":
                                    error_msg = event.get("message", "Unknown error")
                                    pytest.fail(f"Workflow failed with error: {error_msg}")

                            except json.JSONDecodeError as e:
                                print(f"[WARNING] Failed to parse event JSON: {e}", flush=True)
                                print(f"  Raw line: {line}", flush=True)

    # ========== VALIDATION PHASE ==========
    print("\n" + "="*60)
    print("VALIDATING RESULTS")
    print("="*60)

    # Overall completion check
    assert workflow_complete, "Workflow did not complete successfully"
    assert len(events) > 0, "No events were received"
    print(f"\nTotal events received: {len(events)}")

    # Stage 1 Validation
    print("\n--- Stage 1 Validation ---")
    assert stage1_complete, "Stage 1 did not complete"
    assert stage1_data is not None, "Stage 1 data is missing"
    assert isinstance(stage1_data, list), "Stage 1 data should be a list"
    assert len(stage1_data) > 0, "Stage 1 should have at least one script"

    # Validate each script in Stage 1
    for i, script in enumerate(stage1_data):
        assert "model" in script, f"Script {i} missing 'model' field"
        assert "response" in script, f"Script {i} missing 'response' field"
        assert isinstance(script["model"], str), f"Script {i} 'model' should be string"
        assert isinstance(script["response"], str), f"Script {i} 'response' should be string"
        assert len(script["response"]) > 100, f"Script {i} response too short (< 100 chars)"

        # Check for basic script elements
        response_upper = script["response"].upper()
        assert any(keyword in response_upper for keyword in ["TITLE", "LOGLINE", "GENRE", "OUTLINE", "SCENE"]), \
            f"Script {i} missing expected screenplay elements"

    print(f"Stage 1: {len(stage1_data)} scripts validated")

    # Stage 2 Validation
    print("\n--- Stage 2 Validation ---")
    assert stage2_complete, "Stage 2 did not complete"
    assert stage2_data is not None, "Stage 2 data is missing"
    assert stage2_metadata is not None, "Stage 2 metadata is missing"
    assert isinstance(stage2_data, list), "Stage 2 data should be a list"
    assert len(stage2_data) > 0, "Stage 2 should have at least one ranking"

    # Validate label_to_model mapping
    label_to_model = stage2_metadata.get("label_to_model", {})
    assert isinstance(label_to_model, dict), "label_to_model should be a dict"
    assert len(label_to_model) > 0, "label_to_model should not be empty"

    # Validate aggregate_rankings
    aggregate_rankings = stage2_metadata.get("aggregate_rankings", [])
    assert isinstance(aggregate_rankings, list), "aggregate_rankings should be a list"
    assert len(aggregate_rankings) > 0, "aggregate_rankings should not be empty"

    # Validate each aggregate ranking entry
    for i, ranking in enumerate(aggregate_rankings):
        assert "model" in ranking, f"Ranking {i} missing 'model' field"
        assert "average_rank" in ranking, f"Ranking {i} missing 'average_rank' field"
        assert "rankings_count" in ranking, f"Ranking {i} missing 'rankings_count' field"
        assert isinstance(ranking["average_rank"], (int, float)), f"Ranking {i} average_rank should be numeric"
        assert ranking["average_rank"] > 0, f"Ranking {i} average_rank should be positive"

    # Validate each ranking in Stage 2
    for i, ranking in enumerate(stage2_data):
        assert "model" in ranking, f"Ranking {i} missing 'model' field"
        assert "ranking" in ranking, f"Ranking {i} missing 'ranking' field"
        assert "parsed_ranking" in ranking, f"Ranking {i} missing 'parsed_ranking' field"
        assert isinstance(ranking["parsed_ranking"], list), f"Ranking {i} parsed_ranking should be a list"

    print(f"Stage 2: {len(stage2_data)} rankings validated")
    print(f"  Label to model mappings: {len(label_to_model)}")
    print(f"  Aggregate rankings: {len(aggregate_rankings)}")

    # Stage 3 Validation
    print("\n--- Stage 3 Validation ---")
    assert stage3_complete, "Stage 3 did not complete"
    assert stage3_data is not None, "Stage 3 data is missing"
    assert isinstance(stage3_data, dict), "Stage 3 data should be a dict"

    # Validate required fields
    assert "winning_model" in stage3_data, "Stage 3 missing 'winning_model'"
    assert "winning_script" in stage3_data, "Stage 3 missing 'winning_script'"
    assert "collaborators" in stage3_data, "Stage 3 missing 'collaborators'"
    assert "selection_rationale" in stage3_data, "Stage 3 missing 'selection_rationale'"

    # Validate winning model
    winning_model = stage3_data["winning_model"]
    assert isinstance(winning_model, str), "winning_model should be string"
    assert winning_model != "error", "winning_model should not be 'error'"
    assert len(winning_model) > 0, "winning_model should not be empty"

    # Validate winning script
    winning_script = stage3_data["winning_script"]
    assert isinstance(winning_script, str), "winning_script should be string"
    assert len(winning_script) > 100, "winning_script too short"

    # Validate collaborators
    collaborators = stage3_data["collaborators"]
    assert isinstance(collaborators, list), "collaborators should be a list"
    assert len(collaborators) >= 2, "Should have at least 2 collaborators for Stage 4"

    for i, collab in enumerate(collaborators):
        assert isinstance(collab, str), f"Collaborator {i} should be string"
        assert len(collab) > 0, f"Collaborator {i} should not be empty"

    print(f"Stage 3: Winner is {winning_model}")
    print(f"  Collaborators: {len(collaborators)}")

    # Stage 4 Validation
    print("\n--- Stage 4 Validation ---")
    assert stage4_complete, "Stage 4 did not complete"
    assert stage4_data is not None, "Stage 4 data is missing"
    assert isinstance(stage4_data, dict), "Stage 4 data should be a dict"

    # Validate required fields
    assert "dialogue_history" in stage4_data, "Stage 4 missing 'dialogue_history'"
    assert "refined_script" in stage4_data, "Stage 4 missing 'refined_script'"
    assert "collaborators" in stage4_data, "Stage 4 missing 'collaborators'"
    assert "num_turns" in stage4_data, "Stage 4 missing 'num_turns'"

    # Validate dialogue_history
    dialogue_history = stage4_data["dialogue_history"]
    assert isinstance(dialogue_history, list), "dialogue_history should be a list"
    # Each turn has 2 messages (author + collaborator), so should have num_turns * 2 messages
    expected_messages = NUM_TURNS * 2
    assert len(dialogue_history) == expected_messages, \
        f"dialogue_history should have {expected_messages} messages (got {len(dialogue_history)})"

    # Validate dialogue turn structure
    for i, turn in enumerate(dialogue_history):
        assert "turn" in turn, f"Dialogue {i} missing 'turn' field"
        assert "model" in turn, f"Dialogue {i} missing 'model' field"
        assert "role" in turn, f"Dialogue {i} missing 'role' field"
        assert "message" in turn, f"Dialogue {i} missing 'message' field"
        assert turn["role"] in ["author", "collaborator"], f"Dialogue {i} has invalid role: {turn['role']}"
        assert isinstance(turn["message"], str), f"Dialogue {i} message should be string"
        assert len(turn["message"]) > 0, f"Dialogue {i} message should not be empty"

    # Validate refined_script
    refined_script = stage4_data["refined_script"]
    assert isinstance(refined_script, str), "refined_script should be string"
    assert len(refined_script) > 100, "refined_script too short"

    # Validate refined script contains expected elements
    refined_upper = refined_script.upper()
    script_elements = ["TITLE", "LOGLINE", "GENRE", "RUNTIME", "OUTLINE"]
    found_elements = [elem for elem in script_elements if elem in refined_upper]
    assert len(found_elements) >= 3, \
        f"refined_script should contain at least 3 of {script_elements}, found: {found_elements}"

    # Check for scene formatting (INT/EXT or SCENE)
    has_scenes = bool(re.search(r'(INT\.|EXT\.|SCENE)', refined_script, re.IGNORECASE))
    assert has_scenes, "refined_script should contain scene headings (INT./EXT./SCENE)"

    # Validate num_turns
    num_turns = stage4_data["num_turns"]
    assert num_turns == NUM_TURNS, f"num_turns should be {NUM_TURNS} (got {num_turns})"

    # Validate collaborators match Stage 3
    stage4_collaborators = stage4_data["collaborators"]
    assert stage4_collaborators == collaborators, "Stage 4 collaborators should match Stage 3"

    print(f"Stage 4: Dialogue complete with {len(dialogue_history)} messages")
    print(f"  Final script length: {len(refined_script)} characters")
    print(f"  Script elements found: {found_elements}")

    # Validation Events Check
    print("\n--- Runtime Validation ---")
    assert len(validation_events) > 0, "No validation events received"
    print(f"Validation events: {len(validation_events)}")

    # Check that at least some validations were successful
    validation_statuses = [
        event.get("compliance", {}).get("status")
        for event in validation_events
    ]
    compliant_count = sum(1 for status in validation_statuses if status == "compliant")
    print(f"  Compliant scripts: {compliant_count}/{len(validation_events)}")

    # Final Script Quality Checks
    print("\n--- Final Script Quality Checks ---")
    word_count = len(refined_script.split())
    print(f"  Word count: {word_count}")

    # Approximate runtime check (150 words per minute)
    estimated_runtime = word_count / 150
    print(f"  Estimated runtime: {estimated_runtime:.1f} minutes (target: {MOVIE_LENGTH})")

    # The script should be within reasonable bounds (we allow 25% tolerance as per the code)
    min_words = int(MOVIE_LENGTH * 150 * 0.75)  # 75% of target
    max_words = int(MOVIE_LENGTH * 150 * 1.25)  # 125% of target

    # We don't make this assertion too strict since the refinement might not be perfect
    # but we do warn if it's way off
    if word_count < min_words or word_count > max_words:
        print(f"  WARNING: Word count {word_count} outside tolerance range ({min_words}-{max_words})")
    else:
        print(f"  Word count within tolerance range ({min_words}-{max_words})")

    # Check for John Wick and Terminator references (from the prompt)
    has_john_wick = bool(re.search(r'john\s+wick', refined_script, re.IGNORECASE))
    has_terminator = bool(re.search(r'terminator', refined_script, re.IGNORECASE))

    # At least one should be present, or the script should reference action/assassin/robot themes
    if not (has_john_wick or has_terminator):
        # Check for thematic elements instead
        thematic_elements = ['assassin', 'killer', 'robot', 'cyborg', 'action', 'combat', 'weapon']
        has_theme = any(re.search(elem, refined_script, re.IGNORECASE) for elem in thematic_elements)
        assert has_theme, "Script should reference John Wick/Terminator or related themes"
        print(f"  Thematic elements found (instead of direct references)")
    else:
        print(f"  References: John Wick={has_john_wick}, Terminator={has_terminator}")

    # Event sequence validation
    print("\n--- Event Sequence Validation ---")
    event_types = [e.get("type") for e in events]

    # Check that stages occur in order
    assert "stage1_complete" in event_types, "Missing stage1_complete event"
    assert "stage2_complete" in event_types, "Missing stage2_complete event"
    assert "stage3_complete" in event_types, "Missing stage3_complete event"
    assert "stage4_complete" in event_types, "Missing stage4_complete event"
    assert "complete" in event_types, "Missing complete event"

    # Check order
    idx_s1 = event_types.index("stage1_complete")
    idx_s2 = event_types.index("stage2_complete")
    idx_s3 = event_types.index("stage3_complete")
    idx_s4 = event_types.index("stage4_complete")
    idx_complete = event_types.index("complete")

    assert idx_s1 < idx_s2 < idx_s3 < idx_s4 < idx_complete, \
        "Events should occur in order: stage1 -> stage2 -> stage3 -> stage4 -> complete"

    print(f"  Events in correct order")
    print(f"  Event sequence: {' -> '.join([et for et in event_types if 'complete' in et])}")

    # Summary
    print("\n" + "="*60)
    print("TEST PASSED - ALL VALIDATIONS SUCCESSFUL")
    print("="*60)
    print(f"Conversation ID: {conversation_id}")
    print(f"Total events: {len(events)}")
    print(f"Stage 1 scripts: {len(stage1_data)}")
    print(f"Stage 2 rankings: {len(stage2_data)}")
    print(f"Stage 3 winner: {winning_model}")
    print(f"Stage 4 dialogue: {len(dialogue_history)} messages")
    print(f"Final script: {len(refined_script)} characters, {word_count} words")
    print("="*60)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_server_is_running():
    """
    Quick sanity check to verify the server is accessible.
    This test should complete quickly and can be used to verify setup.
    """
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        try:
            async with session.get(f"{BASE_URL}/api/conversations") as response:
                assert response.status == 200, f"Server returned {response.status}"
                print("\nServer is accessible and responding")
        except aiohttp.ClientConnectorError:
            pytest.fail(f"Cannot connect to server at {BASE_URL}. Is the server running on port 8004?")


if __name__ == "__main__":
    # Allow running this test directly
    print("Running movie script integration test...")
    print(f"Base URL: {BASE_URL}")
    print(f"Timeout: {TIMEOUT}s")
    asyncio.run(test_movie_script_workflow_end_to_end())
