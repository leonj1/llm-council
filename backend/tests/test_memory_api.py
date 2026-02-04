"""
Tests for Memory Explorer API endpoints.

Tests that:
1. Memory endpoints require authentication
2. Memory endpoints require admin or superadmin role
3. Non-admin users get 403 Forbidden
4. Endpoints proxy correctly to agent-memory-api
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from backend.main import app
from backend.auth import sessions


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def admin_session():
    """Create an admin session and return session_id."""
    session_id = "test-admin-session-123"
    sessions[session_id] = {
        "email": "admin@example.com",
        "name": "Admin User",
        "picture": "https://example.com/admin.jpg",
        "user_id": 1,
        "role": "admin",
    }
    yield session_id
    # Cleanup
    if session_id in sessions:
        del sessions[session_id]


@pytest.fixture
def superadmin_session():
    """Create a superadmin session and return session_id."""
    session_id = "test-superadmin-session-456"
    sessions[session_id] = {
        "email": "superadmin@example.com",
        "name": "Super Admin",
        "picture": "https://example.com/superadmin.jpg",
        "user_id": 2,
        "role": "superadmin",
    }
    yield session_id
    # Cleanup
    if session_id in sessions:
        del sessions[session_id]


@pytest.fixture
def user_session():
    """Create a regular user session and return session_id."""
    session_id = "test-user-session-789"
    sessions[session_id] = {
        "email": "user@example.com",
        "name": "Regular User",
        "picture": "https://example.com/user.jpg",
        "user_id": 3,
        "role": "user",
    }
    yield session_id
    # Cleanup
    if session_id in sessions:
        del sessions[session_id]


class TestMemoryEndpointsAuth:
    """Test authentication requirements for memory endpoints."""

    def test_list_agents_requires_auth(self, client):
        """GET /api/memories/agents should require authentication."""
        response = client.get("/api/memories/agents")
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    def test_search_memories_requires_auth(self, client):
        """POST /api/memories/search should require authentication."""
        response = client.post(
            "/api/memories/search",
            json={"query": "test"}
        )
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    def test_get_memory_requires_auth(self, client):
        """GET /api/memories/{id} should require authentication."""
        response = client.get("/api/memories/some-id")
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]


class TestMemoryEndpointsAdminAccess:
    """Test that memory endpoints require admin role."""

    def test_list_agents_forbids_regular_user(self, client, user_session):
        """Regular users should not access GET /api/memories/agents."""
        response = client.get(
            "/api/memories/agents",
            cookies={"session_id": user_session}
        )
        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]

    def test_search_memories_forbids_regular_user(self, client, user_session):
        """Regular users should not access POST /api/memories/search."""
        response = client.post(
            "/api/memories/search",
            json={"query": "test"},
            cookies={"session_id": user_session}
        )
        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]

    def test_get_memory_forbids_regular_user(self, client, user_session):
        """Regular users should not access GET /api/memories/{id}."""
        response = client.get(
            "/api/memories/some-id",
            cookies={"session_id": user_session}
        )
        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]


class TestMemoryEndpointsAdminAllowed:
    """Test that admin and superadmin can access memory endpoints."""

    @patch('backend.memory.AGENT_MEMORY_API_TOKEN', 'test-token')
    @patch('backend.memory.httpx.AsyncClient')
    def test_list_agents_allows_admin(self, mock_client_class, client, admin_session):
        """Admin users should access GET /api/memories/agents."""
        # Mock the async client
        mock_client = MagicMock()
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"agent_id": "jarvis-intel"}]
        mock_client.get = AsyncMock(return_value=mock_response)

        response = client.get(
            "/api/memories/agents",
            cookies={"session_id": admin_session}
        )
        
        assert response.status_code == 200
        assert response.json() == [{"agent_id": "jarvis-intel"}]

    @patch('backend.memory.AGENT_MEMORY_API_TOKEN', 'test-token')
    @patch('backend.memory.httpx.AsyncClient')
    def test_list_agents_allows_superadmin(self, mock_client_class, client, superadmin_session):
        """Superadmin users should access GET /api/memories/agents."""
        mock_client = MagicMock()
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"agent_id": "jarvis-macbook"}]
        mock_client.get = AsyncMock(return_value=mock_response)

        response = client.get(
            "/api/memories/agents",
            cookies={"session_id": superadmin_session}
        )
        
        assert response.status_code == 200

    @patch('backend.memory.AGENT_MEMORY_API_TOKEN', 'test-token')
    @patch('backend.memory.httpx.AsyncClient')
    def test_search_memories_allows_admin(self, mock_client_class, client, admin_session):
        """Admin users should access POST /api/memories/search."""
        mock_client = MagicMock()
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "id": "mem-123",
                    "content": "Test memory",
                    "agent_id": "jarvis-intel",
                    "created_at": "2024-01-01T00:00:00Z"
                }
            ]
        }
        mock_client.post = AsyncMock(return_value=mock_response)

        response = client.post(
            "/api/memories/search",
            json={"query": "test", "scope": "network"},
            cookies={"session_id": admin_session}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 1

    @patch('backend.memory.AGENT_MEMORY_API_TOKEN', 'test-token')
    @patch('backend.memory.httpx.AsyncClient')
    def test_get_memory_allows_admin(self, mock_client_class, client, admin_session):
        """Admin users should access GET /api/memories/{id}."""
        mock_client = MagicMock()
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "mem-123",
            "content": "Full memory content",
            "agent_id": "jarvis-intel",
            "created_at": "2024-01-01T00:00:00Z"
        }
        mock_client.get = AsyncMock(return_value=mock_response)

        response = client.get(
            "/api/memories/mem-123",
            cookies={"session_id": admin_session}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "mem-123"


class TestMemoryApiNotConfigured:
    """Test behavior when agent-memory-api is not configured."""

    @patch('backend.memory.AGENT_MEMORY_API_TOKEN', '')
    def test_list_agents_returns_500_without_token(self, client, admin_session):
        """Should return 500 if AGENT_MEMORY_API_TOKEN is not set."""
        response = client.get(
            "/api/memories/agents",
            cookies={"session_id": admin_session}
        )
        
        assert response.status_code == 500
        assert "not configured" in response.json()["detail"]

    @patch('backend.memory.AGENT_MEMORY_API_TOKEN', '')
    def test_search_memories_returns_500_without_token(self, client, admin_session):
        """Should return 500 if AGENT_MEMORY_API_TOKEN is not set."""
        response = client.post(
            "/api/memories/search",
            json={"query": "test"},
            cookies={"session_id": admin_session}
        )
        
        assert response.status_code == 500
        assert "not configured" in response.json()["detail"]


class TestMemorySearchParameters:
    """Test search parameter handling."""

    @patch('backend.memory.AGENT_MEMORY_API_TOKEN', 'test-token')
    @patch('backend.memory.httpx.AsyncClient')
    def test_search_with_filters(self, mock_client_class, client, admin_session):
        """Search should pass optional filters to agent-memory-api."""
        mock_client = MagicMock()
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}
        mock_client.post = AsyncMock(return_value=mock_response)

        response = client.post(
            "/api/memories/search",
            json={
                "query": "test query",
                "scope": "network",
                "limit": 10,
                "agent_id": "jarvis-intel",
                "project_id": "my-project",
                "tags": ["important", "review"]
            },
            cookies={"session_id": admin_session}
        )
        
        assert response.status_code == 200
        
        # Verify the call was made with correct parameters
        mock_client.post.assert_called_once()
        call_kwargs = mock_client.post.call_args
        body = call_kwargs.kwargs["json"]
        
        assert body["query"] == "test query"
        assert body["scope"] == "network"
        assert body["limit"] == 10
        assert body["project_id"] == "my-project"
        assert body["tags"] == ["important", "review"]

    @patch('backend.memory.AGENT_MEMORY_API_TOKEN', 'test-token')
    @patch('backend.memory.httpx.AsyncClient')
    def test_search_with_agent_scope(self, mock_client_class, client, admin_session):
        """Search with agent scope should pass correct X-Agent-ID header."""
        mock_client = MagicMock()
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}
        mock_client.post = AsyncMock(return_value=mock_response)

        response = client.post(
            "/api/memories/search",
            json={
                "query": "test",
                "scope": "mine",
                "agent_id": "jarvis-macbook"
            },
            cookies={"session_id": admin_session}
        )
        
        assert response.status_code == 200
        
        # Verify X-Agent-ID header was set
        call_kwargs = mock_client.post.call_args
        headers = call_kwargs.kwargs["headers"]
        assert headers.get("X-Agent-ID") == "jarvis-macbook"
