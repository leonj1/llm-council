"""Memory Explorer API - Proxy to agent-memory-api (admin only)."""

import os
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
import httpx

from .auth import require_auth

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
