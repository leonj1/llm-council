"""Tests for crawler proxy endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.auth import require_auth
from backend import crawler


@pytest.fixture(autouse=True)
def reset_active_jobs():
    """Ensure in-memory active job tracking is isolated per test."""
    crawler.active_crawl_jobs.clear()
    yield
    crawler.active_crawl_jobs.clear()


@pytest.fixture
def mock_require_auth():
    """Mock authenticated user for crawler endpoints."""
    async def _mock_require_auth():
        return {"user_id": 42, "role": "admin"}

    return _mock_require_auth


@pytest.fixture
def client(mock_require_auth):
    """Create TestClient with mocked auth."""
    app.dependency_overrides[require_auth] = mock_require_auth
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_crawler_status_requires_auth():
    """Crawler status endpoint should require authentication."""
    with TestClient(app) as unauth_client:
        response = unauth_client.get("/api/crawler/status/01TESTULID/1")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]


def test_crawler_status_proxies_to_upstream(client):
    """Status endpoint should proxy to crawler service and return JSON body."""
    with patch("backend.crawler.CRAWLER_SERVICE_URL", "http://crawler.internal"), patch(
        "backend.crawler.httpx.AsyncClient"
    ) as mock_client_class:
        mock_http_client = MagicMock()
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_http_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "target_ulid": "01TESTULID",
            "version": 1,
            "status": "in_progress",
        }
        mock_http_client.get = AsyncMock(return_value=mock_response)

        response = client.get("/api/crawler/status/01TESTULID/1")

        assert response.status_code == 200
        assert response.json()["status"] == "in_progress"
        mock_http_client.get.assert_called_once_with(
            "http://crawler.internal/extract/01TESTULID/1/status"
        )


def test_crawler_status_returns_502_on_connection_error(client):
    """Status endpoint should return 502 when crawler service is unreachable."""
    with patch("backend.crawler.httpx.AsyncClient") as mock_client_class:
        mock_http_client = MagicMock()
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_http_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_http_client.get = AsyncMock(side_effect=httpx.RequestError("connection refused"))

        response = client.get("/api/crawler/status/01TESTULID/1")

        assert response.status_code == 502
        assert "Failed to connect to crawler service" in response.json()["detail"]


def test_crawler_progress_proxies_sse_stream(client):
    """Progress endpoint should stream upstream SSE events."""
    with patch("backend.crawler.CRAWLER_SERVICE_URL", "http://crawler.internal"), patch(
        "backend.crawler.httpx.AsyncClient"
    ) as mock_client_class:
        mock_http_client = MagicMock()
        mock_http_client.build_request.return_value = object()
        mock_http_client.aclose = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_http_client

        stream_response = MagicMock()
        stream_response.status_code = 200
        stream_response.aclose = AsyncMock(return_value=None)
        stream_response.headers = {"content-type": "text/event-stream"}

        async def _iter_bytes():
            yield b'data: {"status":"started"}\n\n'
            yield b'data: {"status":"completed"}\n\n'

        stream_response.aiter_bytes = _iter_bytes
        mock_http_client.send = AsyncMock(return_value=stream_response)

        response = client.get("/api/crawler/progress/01TESTULID/1")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        assert '{"status":"started"}' in response.text
        assert '{"status":"completed"}' in response.text
        assert crawler.active_crawl_jobs == {}
        mock_http_client.send.assert_called_once()


def test_crawler_active_returns_tracked_jobs(client):
    """Active endpoint should return current in-memory job list."""
    crawler.active_crawl_jobs["01TESTULID:1"] = {
        "target_ulid": "01TESTULID",
        "version": 1,
        "started_at": "2026-01-01T00:00:00+00:00",
    }

    response = client.get("/api/crawler/active")

    assert response.status_code == 200
    jobs = response.json()
    assert isinstance(jobs, list)
    assert len(jobs) == 1
    assert jobs[0]["target_ulid"] == "01TESTULID"
