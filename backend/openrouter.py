"""OpenRouter API client for making LLM requests with automatic fallback."""

import logging
import time
import httpx
from typing import List, Dict, Any, Optional
from .config import OPENROUTER_API_KEY, OPENROUTER_API_URL, get_backup_model

logger = logging.getLogger("llm-council.openrouter")

# HTTP status codes that trigger fallback to backup provider
FALLBACK_STATUS_CODES = {
    402,  # Payment Required
    429,  # Too Many Requests (rate limiting)
    503,  # Service Unavailable
}


async def _query_openrouter(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 120.0
) -> tuple[Optional[Dict[str, Any]], Optional[int]]:
    """
    Query a single model via OpenRouter API.

    Returns:
        Tuple of (response_dict, error_status_code)
        - On success: (response_dict, None)
        - On fallback-eligible error: (None, status_code)
        - On other error: (None, None)
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
    }

    model_short = model.split('/')[-1]
    logger.debug(f"[OpenRouter] Querying {model_short} (timeout={timeout}s)...")
    start_time = time.time()

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                OPENROUTER_API_URL,
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            elapsed = time.time() - start_time
            data = response.json()
            message = data['choices'][0]['message']
            content = message.get('content', '')
            word_count = len(content.split()) if content else 0

            logger.debug(f"[OpenRouter] {model_short} responded in {elapsed:.2f}s ({word_count} words)")

            return {
                'content': content,
                'reasoning_details': message.get('reasoning_details'),
                'provider': 'openrouter'
            }, None

    except httpx.HTTPStatusError as e:
        elapsed = time.time() - start_time
        status_code = e.response.status_code
        logger.error(f"[OpenRouter] HTTP {status_code} querying {model_short} after {elapsed:.2f}s: {e}")

        if status_code in FALLBACK_STATUS_CODES:
            return None, status_code
        return None, None

    except httpx.TimeoutException as e:
        elapsed = time.time() - start_time
        logger.error(f"[OpenRouter] TIMEOUT querying {model_short} after {elapsed:.2f}s: {e}")
        return None, None

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[OpenRouter] ERROR querying {model_short} after {elapsed:.2f}s: {e}")
        return None, None


async def query_model(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 120.0,
    use_fallback: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Query a single model via OpenRouter API with automatic fallback to backup provider.

    Args:
        model: Primary model identifier (e.g., "openai/gpt-5.1")
        messages: List of message dicts with 'role' and 'content'
        timeout: Request timeout in seconds
        use_fallback: Whether to try backup provider if primary fails with 402/429

    Returns:
        Response dict with 'content' and optional 'reasoning_details', or None if failed
    """
    # First, try OpenRouter
    result, error_status = await _query_openrouter(model, messages, timeout)

    if result is not None:
        return result

    # If we got a fallback-eligible error and fallback is enabled, try backup provider
    if error_status in FALLBACK_STATUS_CODES and use_fallback:
        backup_config = get_backup_model(model)

        if backup_config:
            from . import requesty

            if requesty.is_requesty_available():
                model_short = model.split('/')[-1]
                backup_model = backup_config["model"]
                backup_model_short = backup_model.split('/')[-1]
                logger.warning(
                    f"[OpenRouter] Falling back to {backup_config['provider']} "
                    f"({backup_model_short}) for {model_short} due to HTTP {error_status}"
                )
                return await requesty.query_model(backup_model, messages, timeout)
            else:
                model_short = model.split('/')[-1]
                logger.warning(
                    f"[OpenRouter] Cannot fallback (REQUESTY_API_KEY not configured) "
                    f"for {model_short}"
                )
        else:
            model_short = model.split('/')[-1]
            logger.warning(
                f"[OpenRouter] No backup provider configured for {model_short}"
            )

    return None


async def query_models_parallel(
    models: List[str],
    messages: List[Dict[str, str]],
    use_fallback: bool = True
) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Query multiple models in parallel with automatic fallback.

    Args:
        models: List of primary model identifiers
        messages: List of message dicts to send to each model
        use_fallback: Whether to try backup provider if primary fails

    Returns:
        Dict mapping model identifier to response dict (or None if failed)
    """
    import asyncio

    # Create tasks for all models
    tasks = [query_model(model, messages, use_fallback=use_fallback) for model in models]

    # Wait for all to complete
    responses = await asyncio.gather(*tasks)

    # Map models to their responses
    return {model: response for model, response in zip(models, responses)}
