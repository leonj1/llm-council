"""Crawler API - proxy endpoints for crawl-url-extractor service."""

import json
import logging
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from .auth import require_auth
from .config import CRAWLER_SERVICE_URL

logger = logging.getLogger("llm-council.crawler")

router = APIRouter(prefix="/api/crawler", tags=["crawler"])
active_crawl_jobs: dict[str, dict] = {}


def _crawler_url(path: str) -> str:
    """Build a crawler service URL from a relative path."""
    return f"{CRAWLER_SERVICE_URL.rstrip('/')}{path}"


def _job_key(target_ulid: str, version: int) -> str:
    return f"{target_ulid}:{version}"


@router.get("/status/{target_ulid}/{version}")
async def get_crawler_status(
    target_ulid: str,
    version: int,
    user: dict = Depends(require_auth),
):
    """Proxy status checks to the crawl-url-extractor service."""
    _ = user  # Required for auth; payload is not otherwise used in this endpoint.
    upstream_url = _crawler_url(f"/extract/{target_ulid}/{version}/status")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(upstream_url)
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to connect to crawler service: {str(exc)}",
            ) from exc

    if response.status_code != 200:
        detail = response.text.strip() or "Unknown crawler service error"
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Crawler service error: {detail}",
        )

    try:
        return response.json()
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=502,
            detail="Crawler service returned invalid JSON for status endpoint",
        ) from exc


@router.get("/progress/{target_ulid}/{version}")
async def get_crawler_progress(
    target_ulid: str,
    version: int,
    user: dict = Depends(require_auth),
):
    """Proxy crawler SSE progress stream."""
    _ = user  # Required for auth; payload is not otherwise used in this endpoint.
    upstream_url = _crawler_url(f"/extract/{target_ulid}/{version}/progress")

    job_key = _job_key(target_ulid, version)
    active_crawl_jobs[job_key] = {
        "target_ulid": target_ulid,
        "version": version,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }

    client = httpx.AsyncClient(timeout=None)
    request = client.build_request("GET", upstream_url)

    try:
        upstream_response = await client.send(request, stream=True)
    except httpx.RequestError as exc:
        active_crawl_jobs.pop(job_key, None)
        await client.aclose()
        raise HTTPException(
            status_code=502,
            detail=f"Failed to connect to crawler service: {str(exc)}",
        ) from exc

    if upstream_response.status_code != 200:
        detail_bytes = await upstream_response.aread()
        detail = detail_bytes.decode("utf-8", errors="replace").strip()
        active_crawl_jobs.pop(job_key, None)
        await upstream_response.aclose()
        await client.aclose()
        raise HTTPException(
            status_code=upstream_response.status_code,
            detail=f"Crawler service error: {detail or 'Unknown crawler service error'}",
        )

    async def event_stream():
        try:
            async for chunk in upstream_response.aiter_bytes():
                if chunk:
                    yield chunk
        except httpx.RequestError as exc:
            logger.warning("Crawler progress stream disconnected: %s", exc)
            error_payload = {
                "status": "error",
                "message": f"Crawler progress stream error: {str(exc)}",
            }
            yield f"data: {json.dumps(error_payload)}\n\n".encode("utf-8")
        finally:
            active_crawl_jobs.pop(job_key, None)
            await upstream_response.aclose()
            await client.aclose()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.get("/active")
async def list_active_crawl_jobs(user: dict = Depends(require_auth)):
    """List active crawler jobs tracked by this backend process."""
    _ = user  # Required for auth; payload is not otherwise used in this endpoint.
    return list(active_crawl_jobs.values())
