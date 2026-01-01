"""Requesty.ai API client for making LLM requests (backup provider)."""

import logging
import time
import httpx
from typing import List, Dict, Any, Optional
from .config import REQUESTY_API_KEY, REQUESTY_API_URL

logger = logging.getLogger("llm-council.requesty")


async def query_model(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 120.0
) -> Optional[Dict[str, Any]]:
    """
    Query a model via Requesty.ai API.

    Args:
        model: Requesty.ai model identifier (e.g., "openai/gpt-5")
        messages: List of message dicts with 'role' and 'content'
        timeout: Request timeout in seconds

    Returns:
        Response dict with 'content' and optional 'reasoning_details', or None if failed
    """
    if not REQUESTY_API_KEY:
        logger.warning("REQUESTY_API_KEY not configured, cannot use Requesty.ai")
        return None

    headers = {
        "Authorization": f"Bearer {REQUESTY_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
    }

    model_short = model.split('/')[-1]
    logger.info(f"[Requesty] Querying {model_short} (timeout={timeout}s)...")
    start_time = time.time()

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                REQUESTY_API_URL,
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            elapsed = time.time() - start_time
            data = response.json()
            message = data['choices'][0]['message']
            content = message.get('content', '')
            word_count = len(content.split()) if content else 0

            logger.info(f"[Requesty] {model_short} responded in {elapsed:.2f}s ({word_count} words)")

            return {
                'content': content,
                'reasoning_details': message.get('reasoning_details'),
                'provider': 'requesty'
            }

    except httpx.TimeoutException as e:
        elapsed = time.time() - start_time
        logger.error(f"[Requesty] TIMEOUT querying {model_short} after {elapsed:.2f}s: {e}")
        return None
    except httpx.HTTPStatusError as e:
        elapsed = time.time() - start_time
        logger.error(f"[Requesty] HTTP {e.response.status_code} querying {model_short} after {elapsed:.2f}s: {e}")
        return None
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[Requesty] ERROR querying {model_short} after {elapsed:.2f}s: {e}")
        return None


def is_requesty_available() -> bool:
    """Check if Requesty.ai is configured and available."""
    return bool(REQUESTY_API_KEY)
