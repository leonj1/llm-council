"""FastAPI backend for LLM Council."""

import logging
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any
import uuid
import json
import asyncio
import os
from pathlib import Path

# Configure verbose logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("llm-council")

from . import storage
from .auth import router as auth_router
from .council import run_full_council, generate_conversation_title, stage1_collect_responses, stage2_collect_rankings, stage3_synthesize_final, calculate_aggregate_rankings
from .movie_script import (
    stage1_generate_scripts,
    stage2_peer_review,
    stage3_select_best_script,
    calculate_script_rankings,
    CollaborativeDialogue,
    validate_and_refine_script,
    check_runtime_compliance
)
from .config import MOVIE_SCRIPT_DEFAULT_TURNS, MOVIE_SCRIPT_MAX_TURNS, CHAIRMAN_MODEL

app = FastAPI(title="LLM Council API")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth router
app.include_router(auth_router)


class CreateConversationRequest(BaseModel):
    """Request to create a new conversation."""
    type: str = "council"  # "council" or "movie_script"


class SendMessageRequest(BaseModel):
    """Request to send a message in a conversation."""
    content: str


class MovieScriptRequest(BaseModel):
    """Request for movie script generation."""
    content: str
    num_turns: int = MOVIE_SCRIPT_DEFAULT_TURNS
    movie_length: int = 90  # Default 90 minutes (feature film)


class ConversationMetadata(BaseModel):
    """Conversation metadata for list view."""
    id: str
    created_at: str
    title: str
    type: str = "council"
    message_count: int


class Conversation(BaseModel):
    """Full conversation with all messages."""
    id: str
    created_at: str
    title: str
    type: str = "council"
    messages: List[Dict[str, Any]]


@app.get("/api")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "LLM Council API"}


@app.get("/api/conversations", response_model=List[ConversationMetadata])
async def list_conversations():
    """List all conversations (metadata only)."""
    return storage.list_conversations()


@app.post("/api/conversations", response_model=Conversation)
async def create_conversation(request: CreateConversationRequest):
    """Create a new conversation."""
    conversation_id = str(uuid.uuid4())
    conversation = storage.create_conversation(conversation_id, request.type)
    return conversation


@app.get("/api/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: str):
    """Get a specific conversation with all its messages."""
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a specific conversation."""
    success = storage.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "deleted", "id": conversation_id}


def extract_conversation_history(messages: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Extract conversation history from messages for context in follow-up queries."""
    history = []
    current_user_query = None

    for msg in messages:
        if msg.get("role") == "user":
            current_user_query = msg.get("content", "")
        elif msg.get("role") == "assistant" and current_user_query:
            # Get the final response (stage3) from the assistant message
            stage3 = msg.get("stage3", {})
            final_response = stage3.get("response", "") if isinstance(stage3, dict) else ""
            if final_response:
                history.append({
                    "user_query": current_user_query,
                    "final_response": final_response
                })
            current_user_query = None

    return history


@app.post("/api/conversations/{conversation_id}/message")
async def send_message(conversation_id: str, request: SendMessageRequest):
    """
    Send a message and run the 3-stage council process.
    Returns the complete response with all stages.
    """
    # Check if conversation exists
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Check if this is the first message
    is_first_message = len(conversation["messages"]) == 0

    # Extract conversation history for follow-up queries
    conversation_history = extract_conversation_history(conversation.get("messages", []))

    # Add user message
    storage.add_user_message(conversation_id, request.content)

    # If this is the first message, generate a title
    if is_first_message:
        title = await generate_conversation_title(request.content)
        storage.update_conversation_title(conversation_id, title)

    # Run the 3-stage council process
    stage1_results, stage2_results, stage3_result, metadata = await run_full_council(
        request.content,
        conversation_history if conversation_history else None
    )

    # Add assistant message with all stages
    storage.add_assistant_message(
        conversation_id,
        stage1_results,
        stage2_results,
        stage3_result
    )

    # Return the complete response with metadata
    return {
        "stage1": stage1_results,
        "stage2": stage2_results,
        "stage3": stage3_result,
        "metadata": metadata
    }


@app.post("/api/conversations/{conversation_id}/message/stream")
async def send_message_stream(conversation_id: str, request: SendMessageRequest):
    """
    Send a message and stream the 3-stage council process.
    Returns Server-Sent Events as each stage completes.
    """
    # Check if conversation exists
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Check if this is the first message
    is_first_message = len(conversation["messages"]) == 0

    # Extract conversation history for follow-up queries
    conversation_history = extract_conversation_history(conversation.get("messages", []))

    async def event_generator():
        try:
            # Add user message
            storage.add_user_message(conversation_id, request.content)

            # Start title generation in parallel (don't await yet)
            title_task = None
            if is_first_message:
                title_task = asyncio.create_task(generate_conversation_title(request.content))

            # Stage 1: Collect responses
            yield f"data: {json.dumps({'type': 'stage1_start'})}\n\n"
            stage1_results = await stage1_collect_responses(request.content, conversation_history if conversation_history else None)
            yield f"data: {json.dumps({'type': 'stage1_complete', 'data': stage1_results})}\n\n"

            # Stage 2: Collect rankings
            yield f"data: {json.dumps({'type': 'stage2_start'})}\n\n"
            stage2_results, label_to_model = await stage2_collect_rankings(request.content, stage1_results)
            aggregate_rankings = calculate_aggregate_rankings(stage2_results, label_to_model)
            yield f"data: {json.dumps({'type': 'stage2_complete', 'data': stage2_results, 'metadata': {'label_to_model': label_to_model, 'aggregate_rankings': aggregate_rankings}})}\n\n"

            # Stage 3: Synthesize final answer
            yield f"data: {json.dumps({'type': 'stage3_start'})}\n\n"
            stage3_result = await stage3_synthesize_final(request.content, stage1_results, stage2_results)
            yield f"data: {json.dumps({'type': 'stage3_complete', 'data': stage3_result})}\n\n"

            # Wait for title generation if it was started
            if title_task:
                title = await title_task
                storage.update_conversation_title(conversation_id, title)
                yield f"data: {json.dumps({'type': 'title_complete', 'data': {'title': title}})}\n\n"

            # Save complete assistant message
            storage.add_assistant_message(
                conversation_id,
                stage1_results,
                stage2_results,
                stage3_result
            )

            # Send completion event
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"

        except Exception as e:
            # Send error event
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.post("/api/conversations/{conversation_id}/movie-script/regenerate-final")
async def regenerate_final_script(conversation_id: str):
    """
    Regenerate the final script for a movie script conversation.
    Uses the stored dialogue history to rebuild context and generate a new final script.
    """
    # Get conversation
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if conversation.get("type") != "movie_script":
        raise HTTPException(status_code=400, detail="Not a movie script conversation")

    # Find the last assistant message with stage4 data
    messages = conversation.get("messages", [])
    assistant_msg = None
    user_prompt = None

    for msg in messages:
        if msg.get("role") == "user":
            user_prompt = msg.get("content", "")
        elif msg.get("role") == "assistant" and msg.get("stage4"):
            assistant_msg = msg

    if not assistant_msg or not user_prompt:
        raise HTTPException(status_code=400, detail="No movie script data found to regenerate")

    stage3 = assistant_msg.get("stage3", {})
    stage4 = assistant_msg.get("stage4", {})
    dialogue_history = stage4.get("dialogue_history", [])
    collaborators = stage4.get("collaborators", stage3.get("collaborators", []))

    if len(collaborators) < 2 or not dialogue_history:
        raise HTTPException(status_code=400, detail="Insufficient dialogue history to regenerate")

    winning_script = stage3.get("winning_script", "")
    # Use current chairman model instead of stored model (which may no longer be available)
    model_to_use = CHAIRMAN_MODEL
    # Keep original model references for context replay
    original_model_a = collaborators[0]

    # Rebuild conversation context from dialogue history
    base_context = f"""You are collaborating on refining a movie script.

Original Request: {user_prompt}

The Winning Script:
{winning_script}

Your goal is to work together to improve this script through constructive dialogue. Focus on:
- Strengthening weak scenes
- Improving dialogue
- Enhancing character development
- Tightening the narrative structure
- Adding cinematic moments

Be specific with your suggestions - reference exact scenes, characters, and dialogue."""

    conversation_context_a = [{"role": "system", "content": base_context}]

    # Replay the dialogue to rebuild context for the author role
    for turn in dialogue_history:
        if turn.get("model") == original_model_a:
            # Original author's turn - they spoke
            if turn.get("turn") == 1:
                prompt = """As the author of this script, review your work and identify 2-3 specific areas you'd like to improve or expand. What aspects could be stronger? Where would you like fresh perspective?"""
            else:
                prompt = """Consider the collaborator's suggestions. Which ideas resonate with you? How would you incorporate them? Are there any suggestions you'd modify or push back on? Share your thoughts and any new ideas that emerged."""
            conversation_context_a.append({"role": "user", "content": prompt})
            conversation_context_a.append({"role": "assistant", "content": turn.get("message", "")})
        else:
            # Collaborator's turn - share with author
            conversation_context_a.append({"role": "user", "content": f"The collaborator suggests:\n\n{turn.get('message', '')}"})

    # Now generate the final script
    from .openrouter import query_model

    final_prompt = """Based on our collaborative discussion, produce the FINAL REFINED SCRIPT.

Incorporate the best ideas from our dialogue. Present the complete refined script in proper screenplay format:

**TITLE:**
**LOGLINE:**
**GENRE:**

**CHARACTERS:**
List each main character with:
- **Name**: Character's name
- **Appearance**: Detailed physical description including:
  - Age and build (height, weight, body type)
  - Facial features (jaw shape, nose, eyes, lips)
  - Hair (color, style, texture - thinning, full, messy, slicked, overgrown, balding)
  - Skin details (complexion, freckles, scars, blemishes, wrinkles, tattoos, birthmarks)
  - Distinctive imperfections or unique features that make them memorable
  - Typical clothing/style
- **Personality**: Key personality traits, motivations, and behavioral characteristics

**REFINED OUTLINE:**
- ACT 1:
- ACT 2:
- ACT 3:

**KEY SCENES:** (Write out the improved/refined key scenes with proper formatting)

**VISUAL NOTES:**
- **Transitions**: Key transition directions between major scenes (FADE IN, CUT TO, DISSOLVE TO, SMASH CUT, MATCH CUT, etc.)
- **B-Roll Suggestions**: Supplemental footage for each act (establishing shots, detail inserts, atmospheric cutaways)
- **Key Camera Directions**: Important shot types for pivotal moments (CLOSE-UP, WIDE SHOT, POV, TRACKING, etc.)

**CINEMATOGRAPHY:** (For each key scene, specify)
- **Camera**: Equipment type (e.g., "ARRI Alexa", "RED Komodo", "iPhone 15 Pro", "35mm Film", "Anamorphic lenses")
- **Lens/Aperture**: Focal length and f-stop (e.g., "50mm at f/1.4 for shallow DOF", "24mm wide at f/8")
- **Contrast Ratio**: Lighting contrast (e.g., "High contrast 8:1 for noir feel", "Low contrast 2:1 for soft daylight")
- **Color/Look**: Color temperature and grade (e.g., "Warm tungsten 3200K", "Desaturated cold tones", "Teal and orange")
- **Frame Rate**: Capture speed (e.g., "24fps standard", "48fps for smooth action", "120fps slow-motion")

**AUDIO NOTES:** (For each key scene, include)
- **Score/Music**: Musical style, mood, tempo (e.g., "Tense synth undertones", "Orchestral crescendo", "Silence for tension")
- **Sound Effects**: Key SFX moments (e.g., "Gunshot echo", "Heartbeat intensifies", "Glass shattering")
- **Ambient Audio**: Environmental soundscape (e.g., "City traffic hum", "Rain on windows", "Distant sirens")

Make this the best version of the script, synthesizing our collaborative improvements."""

    conversation_context_a.append({"role": "user", "content": final_prompt})

    # Use current chairman model to generate final script
    response = await query_model(model_to_use, conversation_context_a, timeout=180.0)

    if response:
        refined_script = response.get('content', 'Unable to generate final script.')
    else:
        raise HTTPException(status_code=500, detail="Failed to generate final script")

    # Update the stored conversation with the new refined script
    stage4["refined_script"] = refined_script
    storage.update_movie_script_stage4(conversation_id, stage4)

    return {
        "status": "success",
        "refined_script": refined_script
    }


@app.post("/api/conversations/{conversation_id}/movie-script/stream")
async def send_movie_script_stream(conversation_id: str, request: MovieScriptRequest):
    """
    Generate a movie script with streaming updates.
    Returns Server-Sent Events as each stage completes.
    """
    workflow_start = time.time()
    logger.info("=" * 60)
    logger.info("MOVIE SCRIPT WORKFLOW STARTED")
    logger.info(f"  Conversation ID: {conversation_id}")
    logger.info(f"  User prompt: {request.content[:100]}...")
    logger.info(f"  Target movie length: {request.movie_length} minutes")
    logger.info(f"  Collaboration turns: {request.num_turns}")
    logger.info("=" * 60)

    # Check if conversation exists
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        logger.error(f"Conversation not found: {conversation_id}")
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Validate num_turns
    num_turns = max(1, min(request.num_turns, MOVIE_SCRIPT_MAX_TURNS))
    movie_length = request.movie_length

    # Check if this is the first message
    is_first_message = len(conversation["messages"]) == 0
    logger.info(f"Is first message: {is_first_message}")

    async def event_generator():
        try:
            # Add user message
            storage.add_user_message(conversation_id, request.content)
            logger.info("User message saved to storage")

            # Start title generation in parallel (don't await yet)
            title_task = None
            if is_first_message:
                logger.info("Starting title generation task (background)")
                title_task = asyncio.create_task(generate_conversation_title(request.content))

            # ========== STAGE 1: Generate Scripts ==========
            logger.info("-" * 50)
            logger.info("STAGE 1: GENERATING SCRIPTS")
            logger.info("-" * 50)
            stage1_start = time.time()
            yield f"data: {json.dumps({'type': 'stage1_start'})}\n\n"
            logger.info("  Querying all council models in parallel...")

            stage1_results = await stage1_generate_scripts(request.content, movie_length)
            stage1_elapsed = time.time() - stage1_start

            logger.info(f"  Stage 1 completed in {stage1_elapsed:.2f}s")
            logger.info(f"  Received {len(stage1_results)} scripts from models:")
            for result in stage1_results:
                word_count = len(result['response'].split())
                logger.info(f"    - {result['model']}: {word_count} words")

            yield f"data: {json.dumps({'type': 'stage1_complete', 'data': stage1_results})}\n\n"

            if not stage1_results:
                logger.error("All models failed to generate scripts!")
                yield f"data: {json.dumps({'type': 'error', 'message': 'All models failed to generate scripts'})}\n\n"
                return

            # ========== STAGE 1.5: Validate Runtime ==========
            logger.info("-" * 50)
            logger.info("STAGE 1.5: VALIDATING RUNTIME COMPLIANCE")
            logger.info("-" * 50)
            validation_start = time.time()
            yield f"data: {json.dumps({'type': 'validation_start', 'stage': 'stage1'})}\n\n"

            refined_stage1_results = []
            for result in stage1_results:
                model = result['model']
                script = result['response']
                logger.info(f"  Validating {model}...")

                # Validate and refine if needed
                refined_script, compliance = await validate_and_refine_script(
                    model, script, movie_length, request.content
                )

                logger.info(f"    Status: {compliance['status']}")
                logger.info(f"    Word count: {compliance['word_count']}")
                logger.info(f"    Estimated runtime: {compliance['estimated_runtime']} min (target: {movie_length} min)")
                if compliance.get('refinement_attempts', 0) > 0:
                    logger.info(f"    Refinement attempts: {compliance['refinement_attempts']}")

                refined_stage1_results.append({
                    'model': model,
                    'response': refined_script,
                    'runtime_validation': compliance
                })

                # Stream validation result for this model
                yield f"data: {json.dumps({'type': 'validation_result', 'model': model, 'compliance': compliance})}\n\n"

            stage1_results = refined_stage1_results
            validation_elapsed = time.time() - validation_start
            logger.info(f"  Stage 1.5 validation completed in {validation_elapsed:.2f}s")
            yield f"data: {json.dumps({'type': 'validation_complete', 'stage': 'stage1'})}\n\n"

            # ========== STAGE 2: Peer Review ==========
            logger.info("-" * 50)
            logger.info("STAGE 2: PEER REVIEW")
            logger.info("-" * 50)
            stage2_start = time.time()
            yield f"data: {json.dumps({'type': 'stage2_start'})}\n\n"
            logger.info("  Models are reviewing and ranking scripts...")

            stage2_results, label_to_model = await stage2_peer_review(request.content, stage1_results)
            aggregate_rankings = calculate_script_rankings(stage2_results, label_to_model)
            stage2_elapsed = time.time() - stage2_start

            logger.info(f"  Stage 2 completed in {stage2_elapsed:.2f}s")
            logger.info(f"  Received {len(stage2_results)} rankings")
            logger.info("  Label to model mapping:")
            for label, model in label_to_model.items():
                logger.info(f"    {label} -> {model}")
            logger.info("  Aggregate rankings:")
            for rank in aggregate_rankings:
                logger.info(f"    {rank['model']}: avg rank {rank['average_rank']:.2f} ({rank['rankings_count']} votes)")

            yield f"data: {json.dumps({'type': 'stage2_complete', 'data': stage2_results, 'metadata': {'label_to_model': label_to_model, 'aggregate_rankings': aggregate_rankings}})}\n\n"

            # ========== STAGE 3: Select Best Script ==========
            logger.info("-" * 50)
            logger.info("STAGE 3: SELECT BEST SCRIPT")
            logger.info("-" * 50)
            stage3_start = time.time()
            yield f"data: {json.dumps({'type': 'stage3_start'})}\n\n"

            stage3_result = await stage3_select_best_script(request.content, stage1_results, aggregate_rankings)
            stage3_elapsed = time.time() - stage3_start

            logger.info(f"  Stage 3 completed in {stage3_elapsed:.2f}s")
            logger.info(f"  Winning model: {stage3_result['winning_model']}")
            logger.info(f"  Collaborators: {stage3_result['collaborators']}")

            yield f"data: {json.dumps({'type': 'stage3_complete', 'data': stage3_result})}\n\n"

            # ========== STAGE 4: Collaborative Dialogue ==========
            logger.info("-" * 50)
            logger.info("STAGE 4: COLLABORATIVE DIALOGUE")
            logger.info("-" * 50)
            stage4_start = time.time()

            stage4_result = {
                "dialogue_history": [],
                "refined_script": stage3_result.get('winning_script', ''),
                "collaborators": stage3_result.get('collaborators', []),
                "num_turns": num_turns
            }

            if len(stage3_result.get('collaborators', [])) >= 2:
                logger.info(f"  Starting {num_turns}-turn collaborative dialogue")
                logger.info(f"  Author (Model A): {stage3_result['collaborators'][0]}")
                logger.info(f"  Collaborator (Model B): {stage3_result['collaborators'][1]}")

                yield f"data: {json.dumps({'type': 'stage4_start', 'data': {'collaborators': stage3_result['collaborators'], 'num_turns': num_turns}})}\n\n"

                dialogue = CollaborativeDialogue(
                    model_a=stage3_result['collaborators'][0],
                    model_b=stage3_result['collaborators'][1],
                    winning_script=stage3_result['winning_script'],
                    user_prompt=request.content,
                    num_turns=num_turns,
                    movie_length=movie_length
                )

                # Stream each dialogue turn
                turn_count = 0
                async for turn_data in dialogue.run_dialogue():
                    turn_count += 1
                    logger.info(f"  Turn {turn_data['turn']} - {turn_data['role']} ({turn_data['model']})")
                    logger.info(f"    Message length: {len(turn_data['message'])} chars")
                    yield f"data: {json.dumps({'type': 'stage4_turn', 'data': turn_data})}\n\n"

                logger.info(f"  Dialogue complete ({turn_count} turns)")
                logger.info("  Generating final refined script...")

                # Generate final refined script
                final_script_start = time.time()
                refined_script = await dialogue.generate_final_script()
                final_script_elapsed = time.time() - final_script_start
                logger.info(f"  Final script generated in {final_script_elapsed:.2f}s")
                logger.info(f"  Final script word count: {len(refined_script.split())}")

                # Validate and refine final script for runtime compliance
                logger.info("  Validating final script runtime...")
                yield f"data: {json.dumps({'type': 'validation_start', 'stage': 'stage4'})}\n\n"

                final_script, final_compliance = await validate_and_refine_script(
                    stage3_result['collaborators'][0],  # Use the author model
                    refined_script,
                    movie_length,
                    request.content
                )

                logger.info(f"  Final script validation:")
                logger.info(f"    Status: {final_compliance['status']}")
                logger.info(f"    Word count: {final_compliance['word_count']}")
                logger.info(f"    Estimated runtime: {final_compliance['estimated_runtime']} min")
                if final_compliance.get('refinement_attempts', 0) > 0:
                    logger.info(f"    Refinement attempts: {final_compliance['refinement_attempts']}")

                yield f"data: {json.dumps({'type': 'validation_result', 'model': 'final_script', 'compliance': final_compliance})}\n\n"
                yield f"data: {json.dumps({'type': 'validation_complete', 'stage': 'stage4'})}\n\n"

                stage4_result = {
                    "dialogue_history": dialogue.dialogue_history,
                    "refined_script": final_script,
                    "collaborators": stage3_result['collaborators'],
                    "num_turns": num_turns,
                    "runtime_validation": final_compliance
                }

                stage4_elapsed = time.time() - stage4_start
                logger.info(f"  Stage 4 completed in {stage4_elapsed:.2f}s")
                yield f"data: {json.dumps({'type': 'stage4_complete', 'data': stage4_result})}\n\n"
            else:
                logger.warning("  Not enough collaborators for Stage 4 dialogue")
                yield f"data: {json.dumps({'type': 'stage4_complete', 'data': stage4_result})}\n\n"

            # Wait for title generation if it was started
            if title_task:
                logger.info("Waiting for title generation to complete...")
                title = await title_task
                storage.update_conversation_title(conversation_id, title)
                logger.info(f"Title generated: {title}")
                yield f"data: {json.dumps({'type': 'title_complete', 'data': {'title': title}})}\n\n"

            # Save complete assistant message
            logger.info("Saving complete assistant message to storage...")
            storage.add_movie_script_message(
                conversation_id,
                stage1_results,
                stage2_results,
                stage3_result,
                stage4_result
            )

            # Send completion event
            workflow_elapsed = time.time() - workflow_start
            logger.info("=" * 60)
            logger.info("MOVIE SCRIPT WORKFLOW COMPLETED")
            logger.info(f"  Total time: {workflow_elapsed:.2f}s")
            logger.info("=" * 60)
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"

        except Exception as e:
            logger.exception(f"Error in movie script workflow: {e}")
            # Send error event
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


# Mount static files for frontend (if available)
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
