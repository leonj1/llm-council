"""
Integration tests for authentication and user persistence flow.

Tests that:
1. OAuth callback fails if database user creation fails
2. User is persisted to database on successful OAuth
3. Session contains valid user_id after successful OAuth
4. Chat creation requires valid user_id from database
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from fastapi.responses import RedirectResponse

from backend.main import app
from backend.auth import require_auth, sessions
from backend import database


class TestOAuthCallbackFailsWithoutDatabase:
    """
    Test that OAuth callback redirects with error if database is unavailable.
    This prevents sessions with null user_id.
    """

    @patch('backend.auth.upsert_user')
    @patch('backend.auth.httpx.AsyncClient')
    def test_oauth_callback_redirects_with_error_when_db_unavailable(
        self, mock_async_client, mock_upsert_user
    ):
        """OAuth callback should redirect with error if upsert_user returns None."""
        # Arrange
        mock_upsert_user.return_value = None  # Simulate DB failure

        # Mock the httpx client for Google OAuth
        mock_client_instance = MagicMock()
        mock_async_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_async_client.return_value.__aexit__ = AsyncMock(return_value=None)

        # Mock token exchange
        mock_token_response = MagicMock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {"access_token": "fake_token"}

        # Mock userinfo response
        mock_userinfo_response = MagicMock()
        mock_userinfo_response.status_code = 200
        mock_userinfo_response.json.return_value = {
            "id": "google123",
            "email": "test@example.com",
            "name": "Test User",
            "picture": "https://example.com/pic.jpg"
        }

        mock_client_instance.post = AsyncMock(return_value=mock_token_response)
        mock_client_instance.get = AsyncMock(return_value=mock_userinfo_response)

        # Add valid state to oauth_states
        from backend.auth import oauth_states
        oauth_states["valid_state"] = True

        client = TestClient(app, follow_redirects=False)

        # Act
        response = client.get("/api/auth/google/callback?code=fake_code&state=valid_state")

        # Assert
        assert response.status_code == 307, f"Expected redirect, got {response.status_code}"
        location = response.headers.get("location", "")
        assert "error=database_unavailable" in location, f"Expected database_unavailable error in redirect, got: {location}"


class TestOAuthCallbackSucceedsWithDatabase:
    """
    Test that OAuth callback succeeds and creates session with valid user_id.
    """

    @patch('backend.auth.upsert_user')
    @patch('backend.auth.httpx.AsyncClient')
    def test_oauth_callback_creates_session_with_user_id(
        self, mock_async_client, mock_upsert_user
    ):
        """OAuth callback should create session with user_id from database."""
        # Arrange
        expected_user_id = 42
        mock_upsert_user.return_value = {
            "id": expected_user_id,
            "google_id": "google123",
            "email": "test@example.com",
            "name": "Test User",
            "picture_url": "https://example.com/pic.jpg"
        }

        # Mock the httpx client for Google OAuth
        mock_client_instance = MagicMock()
        mock_async_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_async_client.return_value.__aexit__ = AsyncMock(return_value=None)

        # Mock token exchange
        mock_token_response = MagicMock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {"access_token": "fake_token"}

        # Mock userinfo response
        mock_userinfo_response = MagicMock()
        mock_userinfo_response.status_code = 200
        mock_userinfo_response.json.return_value = {
            "id": "google123",
            "email": "test@example.com",
            "name": "Test User",
            "picture": "https://example.com/pic.jpg"
        }

        mock_client_instance.post = AsyncMock(return_value=mock_token_response)
        mock_client_instance.get = AsyncMock(return_value=mock_userinfo_response)

        # Add valid state to oauth_states
        from backend.auth import oauth_states
        oauth_states["valid_state_2"] = True

        # Clear existing sessions
        sessions.clear()

        client = TestClient(app, follow_redirects=False)

        # Act
        response = client.get("/api/auth/google/callback?code=fake_code&state=valid_state_2")

        # Assert
        assert response.status_code == 307, f"Expected redirect, got {response.status_code}"
        location = response.headers.get("location", "")
        assert "/chat" in location, f"Expected redirect to /chat, got: {location}"
        assert "error" not in location, f"Should not have error in redirect: {location}"

        # Verify session was created with user_id
        assert len(sessions) == 1, "Expected exactly one session"
        session_data = list(sessions.values())[0]
        assert session_data["user_id"] == expected_user_id, f"Expected user_id={expected_user_id}, got {session_data['user_id']}"
        assert session_data["email"] == "test@example.com"


class TestChatCreationRequiresValidUser:
    """
    Integration test: Chat creation requires user to exist in database.
    """

    def test_create_chat_with_valid_user_succeeds(self):
        """Creating a chat with valid user_id should succeed."""
        # First create a user in the database
        user = database.upsert_user(
            google_id="integration_test_user",
            email="integration@test.com",
            name="Integration Test",
            picture_url=None
        )

        if user is None:
            pytest.skip("Database not available for integration test")

        # Now create a chat for this user
        chat = database.create_chat(user["id"])

        # Assert
        assert chat is not None, "Chat should be created successfully"
        assert chat["user_id"] == user["id"]
        assert chat["id"] is not None
        assert chat["title"] == "New Conversation"

    def test_create_chat_with_nonexistent_user_fails(self):
        """Creating a chat with non-existent user_id should fail with FK constraint."""
        # Try to create a chat with a user_id that doesn't exist
        nonexistent_user_id = 99999

        # This should raise an IntegrityError due to FK constraint
        with pytest.raises(Exception) as exc_info:
            database.create_chat(nonexistent_user_id)

        # The error should be related to foreign key constraint
        error_msg = str(exc_info.value).lower()
        assert "foreign key" in error_msg or "constraint" in error_msg or "1452" in error_msg


class TestMessageCreationRequiresValidChat:
    """
    Integration test: Message creation requires chat to exist with valid user.
    """

    def test_create_message_with_valid_chat_succeeds(self):
        """Creating a message in a valid chat should succeed."""
        # Create user first
        user = database.upsert_user(
            google_id="msg_test_user",
            email="msgtest@test.com",
            name="Message Test",
            picture_url=None
        )

        if user is None:
            pytest.skip("Database not available for integration test")

        # Create chat
        chat = database.create_chat(user["id"])
        assert chat is not None

        # Create message
        message = database.create_message(
            chat_id=chat["id"],
            role="user",
            content="Hello, this is a test message",
            stage1_data=None,
            stage2_data=None,
            stage3_data=None
        )

        # Assert
        assert message is not None, "Message should be created successfully"
        assert message["chat_id"] == chat["id"]
        assert message["role"] == "user"
        assert message["content"] == "Hello, this is a test message"


class TestFullAuthToMessageFlow:
    """
    End-to-end integration test: User auth -> Chat creation -> Message creation.
    """

    def test_full_flow_user_to_message(self):
        """Test complete flow from user creation to message persistence."""
        # Step 1: Create user (simulating OAuth callback)
        user = database.upsert_user(
            google_id="full_flow_user",
            email="fullflow@test.com",
            name="Full Flow Test",
            picture_url="https://example.com/pic.jpg"
        )

        if user is None:
            pytest.skip("Database not available for integration test")

        assert user["id"] is not None
        assert user["email"] == "fullflow@test.com"

        # Step 2: Create chat for this user
        chat = database.create_chat(user["id"])
        assert chat is not None
        assert chat["user_id"] == user["id"]

        # Step 3: Add user message
        user_msg = database.create_message(
            chat_id=chat["id"],
            role="user",
            content="What is the meaning of life?",
            stage1_data=None,
            stage2_data=None,
            stage3_data=None
        )
        assert user_msg is not None
        assert user_msg["role"] == "user"

        # Step 4: Add assistant message with stage data
        stage1_data = [{"model": "gpt-4", "response": "Test response"}]
        stage2_data = [{"model": "gpt-4", "ranking": "A: 1, B: 2"}]
        stage3_data = {"response": "42 is the answer"}

        assistant_msg = database.create_message(
            chat_id=chat["id"],
            role="assistant",
            content="42 is the answer",
            stage1_data=stage1_data,
            stage2_data=stage2_data,
            stage3_data=stage3_data
        )
        assert assistant_msg is not None
        assert assistant_msg["role"] == "assistant"
        assert assistant_msg["stage1_data"] == stage1_data
        assert assistant_msg["stage2_data"] == stage2_data
        assert assistant_msg["stage3_data"] == stage3_data

        # Step 5: Verify we can retrieve all messages
        messages = database.get_messages_by_chat_id(chat["id"])
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"

        # Step 6: Verify chat retrieval
        retrieved_chat = database.get_chat_by_id(chat["id"])
        assert retrieved_chat is not None
        assert retrieved_chat["user_id"] == user["id"]
