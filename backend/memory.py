"""Memory Explorer API - Proxy to agent-memory-api (admin only)."""

import os
import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
import httpx

from .auth import require_auth
from .openrouter import query_model

logger = logging.getLogger("llm-council.memory")

router = APIRouter(prefix="/api/memories", tags=["memories"])

# Agent Memory API configuration from environment
AGENT_MEMORY_API_URL = os.getenv("AGENT_MEMORY_API_URL", "https://api-production-0d67.up.railway.app")
AGENT_MEMORY_API_TOKEN = os.getenv("AGENT_MEMORY_API_TOKEN", "")


class MemorySearchRequest(BaseModel):
    """Request body for memory search."""
    query: str
    scope: str = "network"  # "mine" | "network" | "agent:agent-name"
    limit: int = 20
    agent_id: Optional[str] = None  # For X-Agent-ID header
    project_id: Optional[str] = None
    tags: Optional[List[str]] = None


class MemorySearchResponse(BaseModel):
    """Single memory result."""
    id: str
    content: str
    agent_id: str
    project_id: Optional[str] = None
    tags: Optional[List[str]] = None
    created_at: str
    score: Optional[float] = None


def require_admin(user: dict = Depends(require_auth)) -> dict:
    """
    Dependency that requires admin or superadmin role.
    
    Args:
        user: User dict from session (via require_auth)
        
    Returns:
        User dict if authorized
        
    Raises:
        HTTPException: 403 if user is not admin/superadmin
    """
    role = user.get("role", "user")
    if role not in ("admin", "superadmin"):
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return user


def _get_headers(agent_id: Optional[str] = None) -> dict:
    """Get headers for agent-memory-api requests."""
    headers = {
        "Authorization": f"Bearer {AGENT_MEMORY_API_TOKEN}",
        "Content-Type": "application/json",
    }
    if agent_id:
        headers["X-Agent-ID"] = agent_id
    return headers


@router.get("/agents")
async def list_agents(user: dict = Depends(require_admin)):
    """
    List all agents with memories.
    
    Returns list of agent IDs that have stored memories.
    Requires admin or superadmin role.
    """
    if not AGENT_MEMORY_API_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="Agent Memory API not configured"
        )
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{AGENT_MEMORY_API_URL}/agents",
                headers=_get_headers()
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Agent Memory API error: {response.text}"
                )
            
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to connect to Agent Memory API: {str(e)}"
            )


@router.post("/search")
async def search_memories(
    request: MemorySearchRequest,
    user: dict = Depends(require_admin)
):
    """
    Search memories across the agent network.
    
    Requires admin or superadmin role.
    """
    if not AGENT_MEMORY_API_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="Agent Memory API not configured"
        )
    
    # Build request body
    body = {
        "query": request.query,
        "scope": request.scope,
        "limit": request.limit,
    }
    
    # Add optional filters
    if request.project_id:
        body["project_id"] = request.project_id
    if request.tags:
        body["tags"] = request.tags
    
    # Determine agent_id for header
    agent_id = request.agent_id or "llm-council"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{AGENT_MEMORY_API_URL}/search",
                headers=_get_headers(agent_id),
                json=body
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Agent Memory API error: {response.text}"
                )
            
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to connect to Agent Memory API: {str(e)}"
            )


@router.get("/{memory_id}")
async def get_memory(
    memory_id: str,
    user: dict = Depends(require_admin)
):
    """
    Get a specific memory by ID.
    
    Requires admin or superadmin role.
    """
    if not AGENT_MEMORY_API_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="Agent Memory API not configured"
        )
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{AGENT_MEMORY_API_URL}/memory/{memory_id}",
                headers=_get_headers()
            )
            
            if response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail="Memory not found"
                )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Agent Memory API error: {response.text}"
                )
            
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to connect to Agent Memory API: {str(e)}"
            )


# Model for AI synthesis - Claude Opus 4.5 via OpenRouter
SYNTHESIS_MODEL = "anthropic/claude-opus-4.5"

# Quality filtering thresholds by match type (Option #4: Floor + Cap)
MIN_SCORES = {
    "vector": 0.2,    # semantic similarity threshold
    "keyword": 0.001  # ts_rank threshold
}
MAX_MEMORIES_FOR_SYNTHESIS = 5  # cap at top N high-quality results


def filter_memories_by_quality(memories: List[dict]) -> tuple[List[dict], dict]:
    """
    Filter memories by score threshold based on match type, then cap at max.
    
    Args:
        memories: List of memory dicts with optional 'score' and 'match_type' fields
        
    Returns:
        Tuple of (filtered_memories, stats_dict)
        stats_dict contains: total_received, passed_threshold, used_for_synthesis, filtered_out
    """
    total_received = len(memories)
    
    # Filter by match type threshold
    passed_threshold = []
    for memory in memories:
        score = memory.get("score")
        match_type = memory.get("match_type", "vector")  # default to vector if not specified
        
        # If no score, include it (benefit of doubt)
        if score is None:
            passed_threshold.append(memory)
            continue
        
        min_score = MIN_SCORES.get(match_type, 0)
        if score >= min_score:
            passed_threshold.append(memory)
    
    # Sort by score descending (highest quality first) and cap
    passed_threshold.sort(key=lambda m: m.get("score") or 0, reverse=True)
    filtered = passed_threshold[:MAX_MEMORIES_FOR_SYNTHESIS]
    
    stats = {
        "total_received": total_received,
        "passed_threshold": len(passed_threshold),
        "used_for_synthesis": len(filtered),
        "filtered_out": total_received - len(filtered)
    }
    
    return filtered, stats


class MemorySynthesizeRequest(BaseModel):
    """Request body for memory synthesis."""
    query: str
    memories: List[dict]  # List of memory objects with content, agent_id, etc.


class MemorySynthesizeResponse(BaseModel):
    """Response from memory synthesis."""
    answer: str
    model: str
    # Quality filtering metadata
    memories_used: int = 0
    memories_total: int = 0
    memories_filtered_out: int = 0


@router.post("/synthesize", response_model=MemorySynthesizeResponse)
async def synthesize_memories(
    request: MemorySynthesizeRequest,
    user: dict = Depends(require_admin)
):
    """
    Synthesize an answer from memory search results using Claude Opus 4.5.
    
    Takes the user's original query and the memory search results,
    sends them to Claude Opus 4.5 to generate a coherent answer.
    
    Quality filtering is applied:
    - Vector matches require score >= 0.2
    - Keyword matches require score >= 0.001
    - Maximum 5 high-quality memories are used
    
    Requires admin or superadmin role.
    """
    if not request.memories:
        raise HTTPException(
            status_code=400,
            detail="No memories provided for synthesis"
        )
    
    # Apply quality filtering
    filtered_memories, filter_stats = filter_memories_by_quality(request.memories)
    
    logger.info(
        f"Quality filter: {filter_stats['total_received']} received, "
        f"{filter_stats['passed_threshold']} passed threshold, "
        f"{filter_stats['used_for_synthesis']} used for synthesis"
    )
    
    # If no memories pass the quality threshold, return early
    if not filtered_memories:
        return MemorySynthesizeResponse(
            answer="No high-quality memories found for this query. The search returned results, but none met the relevance threshold for synthesis.",
            model=SYNTHESIS_MODEL,
            memories_used=0,
            memories_total=filter_stats["total_received"],
            memories_filtered_out=filter_stats["filtered_out"]
        )
    
    # Build the context from filtered memories
    memory_context_parts = []
    for i, memory in enumerate(filtered_memories, 1):
        content = memory.get("content", "")
        agent_id = memory.get("agent_id", "unknown")
        created_at = memory.get("created_at", "unknown date")
        project_id = memory.get("project_id", "")
        tags = memory.get("tags", [])
        
        memory_entry = f"**Memory {i}** (Agent: {agent_id}, Date: {created_at})"
        if project_id:
            memory_entry += f" [Project: {project_id}]"
        if tags:
            memory_entry += f" [Tags: {', '.join(tags)}]"
        memory_entry += f"\n{content}"
        memory_context_parts.append(memory_entry)
    
    memory_context = "\n\n---\n\n".join(memory_context_parts)
    
    # Build the prompt for Claude
    system_prompt = """You are an AI assistant helping to synthesize information from agent memories.
Your task is to analyze the provided memories and answer the user's question based on the information contained within them.

Guidelines:
- Focus on providing a direct, helpful answer to the user's question
- Cite specific memories when relevant (e.g., "According to Memory 3...")
- If the memories don't contain enough information to fully answer the question, say so
- Highlight any contradictions or discrepancies between memories if they exist
- Be concise but thorough
- Format your response with clear structure using markdown when appropriate"""

    user_message = f"""**User Question:** {request.query}

**Relevant Memories:**

{memory_context}

Based on these memories, please answer the user's question."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]
    
    logger.info(f"Synthesizing answer for query: {request.query[:100]}... using {len(filtered_memories)} of {filter_stats['total_received']} memories")
    
    try:
        response = await query_model(SYNTHESIS_MODEL, messages, timeout=120.0)
        
        if response is None:
            logger.error("Failed to get response from synthesis model")
            raise HTTPException(
                status_code=502,
                detail="Failed to generate synthesis - model did not respond"
            )
        
        answer = response.get("content", "")
        if not answer:
            raise HTTPException(
                status_code=502,
                detail="Failed to generate synthesis - empty response"
            )
        
        logger.info(f"Synthesis complete: {len(answer)} characters")
        
        return MemorySynthesizeResponse(
            answer=answer,
            model=SYNTHESIS_MODEL,
            memories_used=filter_stats["used_for_synthesis"],
            memories_total=filter_stats["total_received"],
            memories_filtered_out=filter_stats["filtered_out"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error during memory synthesis: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Synthesis failed: {str(e)}"
        )
