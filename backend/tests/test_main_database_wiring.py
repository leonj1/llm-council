"""
BDD Tests for Main API Database Wiring
Tests derived from Gherkin scenarios for Main API uses database for persistence

Feature: Main API uses database for persistence
  As a user of the LLM Council
  I want my conversations stored in the database
  So that my chat history persists reliably
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from fastapi.testclient import TestClient


@pytest.fixture
def mock_auth_user():
    """Return mock authenticated user data."""
    return {"email": "test@example.com", "name": "Test User", "picture": None, "user_id": 42}


@pytest.fixture
def mock_require_auth(mock_auth_user):
    """Create a mock require_auth dependency that returns the mock user."""
    async def _mock_require_auth():
        return mock_auth_user
    return _mock_require_auth


@pytest.fixture
def client_with_mocked_auth(mock_require_auth):
    """Create TestClient with mocked authentication."""
    from backend.main import app
    from backend.auth import require_auth

    app.dependency_overrides[require_auth] = mock_require_auth
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestCreateConversationStoresToDatabase:
    """
    Scenario: Create conversation stores to database
    Given a user is authenticated
    When the user creates a new conversation
    Then the conversation is stored in the database
    And the response contains a conversation identifier
    """

    @patch('backend.main.database.create_chat')
    def test_create_conversation_calls_database_create_chat(
        self, mock_create_chat, client_with_mocked_auth, mock_auth_user
    ):
        """Test that creating a conversation calls database.create_chat."""
        # Arrange
        mock_create_chat.return_value = {
            "id": "test-uuid-123",
            "user_id": mock_auth_user["user_id"],
            "created_at": "2024-01-15T10:00:00",
            "title": "New Conversation",
            "type": "council"
        }

        # Act
        response = client_with_mocked_auth.post("/api/conversations")

        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        mock_create_chat.assert_called_once_with(mock_auth_user["user_id"])

    @patch('backend.main.database.create_chat')
    def test_create_conversation_response_contains_id(
        self, mock_create_chat, client_with_mocked_auth, mock_auth_user
    ):
        """Test that the response contains a conversation identifier."""
        # Arrange
        expected_id = "abc123-conversation-id"
        mock_create_chat.return_value = {
            "id": expected_id,
            "user_id": mock_auth_user["user_id"],
            "created_at": "2024-01-15T10:00:00",
            "title": "New Conversation",
            "type": "council"
        }

        # Act
        response = client_with_mocked_auth.post("/api/conversations")

        # Assert
        assert response.status_code == 200
        response_json = response.json()
        assert "id" in response_json, "Response must contain 'id' field"
        assert response_json["id"] == expected_id


class TestAddUserMessageStoresToDatabase:
    """
    Scenario: Add user message stores with user role
    """

    @patch('backend.main.database.create_message')
    @patch('backend.main.database.update_chat_title')
    @patch('backend.main.run_full_council')
    @patch('backend.main.generate_conversation_title')
    @patch('backend.main.database.get_messages_by_chat_id')
    @patch('backend.main.database.get_chat_by_id')
    def test_send_message_stores_user_message_with_user_role(
        self,
        mock_get_chat,
        mock_get_messages,
        mock_gen_title,
        mock_run_council,
        mock_update_title,
        mock_create_message,
        client_with_mocked_auth,
        mock_auth_user
    ):
        """Test that sending a message stores it with role='user'."""
        # Arrange
        conversation_id = "abc123"

        mock_get_chat.return_value = {
            "id": conversation_id,
            "user_id": mock_auth_user["user_id"],
            "created_at": "2024-01-15T10:00:00",
            "title": "Test Conversation",
            "type": "council"
        }
        mock_get_messages.return_value = [{"role": "user", "content": "previous"}]

        mock_run_council.return_value = (
            [{"model": "test", "response": "test"}],
            [{"model": "test", "ranking": "A"}],
            {"response": "Final answer"},
            {"label_to_model": {}}
        )

        # Act
        response = client_with_mocked_auth.post(
            f"/api/conversations/{conversation_id}/message",
            json={"content": "Hello"}
        )

        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        # Verify create_message was called for user message
        calls = mock_create_message.call_args_list
        assert len(calls) >= 1, "create_message should be called at least once"

        # First call should be user message
        user_call = calls[0]
        assert user_call.args[0] == conversation_id
        assert user_call.args[1] == "user"
        assert user_call.args[2] == "Hello"


class TestAddAssistantMessageStoresStageDataSeparately:
    """
    Scenario: Add assistant message stores stage data separately
    """

    @patch('backend.main.database.create_message')
    @patch('backend.main.run_full_council')
    @patch('backend.main.database.get_messages_by_chat_id')
    @patch('backend.main.database.get_chat_by_id')
    def test_assistant_message_stores_stage_data(
        self,
        mock_get_chat,
        mock_get_messages,
        mock_run_council,
        mock_create_message,
        client_with_mocked_auth,
        mock_auth_user
    ):
        """Test that assistant messages store stage1, stage2, stage3 data separately."""
        # Arrange
        conversation_id = "abc123"
        stage1_data = [{"model": "gpt-4", "response": "Stage 1 response"}]
        stage2_data = [{"model": "gpt-4", "ranking": "Response A: 1"}]
        stage3_data = {"response": "Final synthesized answer"}

        mock_get_chat.return_value = {
            "id": conversation_id,
            "user_id": mock_auth_user["user_id"],
            "created_at": "2024-01-15T10:00:00",
            "title": "Test Conversation",
            "type": "council"
        }
        mock_get_messages.return_value = [{"role": "user", "content": "previous"}]

        mock_run_council.return_value = (
            stage1_data,
            stage2_data,
            stage3_data,
            {"label_to_model": {}}
        )

        # Act
        response = client_with_mocked_auth.post(
            f"/api/conversations/{conversation_id}/message",
            json={"content": "What is AI?"}
        )

        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        # Verify create_message was called for assistant message with stage data
        calls = mock_create_message.call_args_list
        assert len(calls) >= 2, "create_message should be called for user and assistant"

        # Second call should be assistant message with stage data
        assistant_call = calls[1]
        assert assistant_call.args[0] == conversation_id
        assert assistant_call.args[1] == "assistant"
        # Content should be from stage3 response
        assert assistant_call.args[2] == "Final synthesized answer"
        # Stage data should be passed as separate arguments
        assert assistant_call.args[3] == stage1_data
        assert assistant_call.args[4] == stage2_data
        assert assistant_call.args[5] == stage3_data


class TestGetConversationRetrievesFromDatabase:
    """
    Scenario: Get conversation retrieves from database
    """

    @patch('backend.main.database.get_messages_by_chat_id')
    @patch('backend.main.database.get_chat_by_id')
    def test_get_conversation_calls_database(
        self,
        mock_get_chat,
        mock_get_messages,
        client_with_mocked_auth,
        mock_auth_user
    ):
        """Test that getting a conversation calls database.get_chat_by_id."""
        # Arrange
        conversation_id = "abc123"
        mock_get_chat.return_value = {
            "id": conversation_id,
            "user_id": mock_auth_user["user_id"],
            "created_at": "2024-01-15T10:00:00",
            "title": "Test Conversation",
            "type": "council"
        }
        mock_get_messages.return_value = []

        # Act
        response = client_with_mocked_auth.get(f"/api/conversations/{conversation_id}")

        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        mock_get_chat.assert_called_with(conversation_id)

    @patch('backend.main.database.get_messages_by_chat_id')
    @patch('backend.main.database.get_chat_by_id')
    def test_get_conversation_response_uses_id_field(
        self,
        mock_get_chat,
        mock_get_messages,
        client_with_mocked_auth,
        mock_auth_user
    ):
        """Test that the response uses 'id' as the identifier field."""
        # Arrange
        conversation_id = "abc123"
        mock_get_chat.return_value = {
            "id": conversation_id,
            "user_id": mock_auth_user["user_id"],
            "created_at": "2024-01-15T10:00:00",
            "title": "Test Conversation",
            "type": "council"
        }
        mock_get_messages.return_value = []

        # Act
        response = client_with_mocked_auth.get(f"/api/conversations/{conversation_id}")

        # Assert
        assert response.status_code == 200
        response_json = response.json()
        assert "id" in response_json, "Response must use 'id' as identifier field"
        assert response_json["id"] == conversation_id

    @patch('backend.main.database.get_messages_by_chat_id')
    @patch('backend.main.database.get_chat_by_id')
    def test_get_conversation_includes_all_messages(
        self,
        mock_get_chat,
        mock_get_messages,
        client_with_mocked_auth,
        mock_auth_user
    ):
        """Test that all messages for the conversation are included in response."""
        # Arrange
        conversation_id = "abc123"
        mock_get_chat.return_value = {
            "id": conversation_id,
            "user_id": mock_auth_user["user_id"],
            "created_at": "2024-01-15T10:00:00",
            "title": "Test Conversation",
            "type": "council"
        }
        expected_messages = [
            {"role": "user", "content": "What is AI?", "stage1_data": None, "stage2_data": None, "stage3_data": None},
            {"role": "assistant", "content": "AI is...", "stage1_data": [{"model": "gpt-4"}], "stage2_data": [{"ranking": "A"}], "stage3_data": {"response": "Final"}}
        ]
        mock_get_messages.return_value = expected_messages

        # Act
        response = client_with_mocked_auth.get(f"/api/conversations/{conversation_id}")

        # Assert
        assert response.status_code == 200
        response_json = response.json()
        assert "messages" in response_json, "Response must contain 'messages' field"
        assert len(response_json["messages"]) == 2

    @patch('backend.main.database.get_chat_by_id')
    def test_get_nonexistent_conversation_returns_404(
        self,
        mock_get_chat,
        client_with_mocked_auth
    ):
        """Test that requesting a non-existent conversation returns 404."""
        # Arrange
        mock_get_chat.return_value = None

        # Act
        response = client_with_mocked_auth.get("/api/conversations/nonexistent-123")

        # Assert
        assert response.status_code == 404


class TestDatabasePersistenceBackground:
    """Background tests for database persistence."""

    @patch('backend.main.database.get_chats_by_user_id')
    def test_list_conversations_calls_database(
        self,
        mock_get_chats,
        client_with_mocked_auth,
        mock_auth_user
    ):
        """Test that listing conversations uses database layer."""
        # Arrange
        mock_get_chats.return_value = [
            {"id": "conv1", "created_at": "2024-01-15T10:00:00", "title": "Conv 1", "type": "council", "message_count": 2}
        ]

        # Act
        response = client_with_mocked_auth.get("/api/conversations")

        # Assert
        assert response.status_code == 200
        mock_get_chats.assert_called_once_with(mock_auth_user["user_id"])

    @patch('backend.main.database.delete_chat')
    @patch('backend.main.database.get_chat_by_id')
    def test_delete_conversation_calls_database(
        self,
        mock_get_chat,
        mock_delete_chat,
        client_with_mocked_auth,
        mock_auth_user
    ):
        """Test that deleting a conversation uses database layer."""
        # Arrange
        conversation_id = "to-delete-123"
        mock_get_chat.return_value = {
            "id": conversation_id,
            "user_id": mock_auth_user["user_id"],
            "created_at": "2024-01-15T10:00:00",
            "title": "To Delete",
            "type": "council"
        }
        mock_delete_chat.return_value = True

        # Act
        response = client_with_mocked_auth.delete(f"/api/conversations/{conversation_id}")

        # Assert
        assert response.status_code == 200
        mock_delete_chat.assert_called_once_with(conversation_id)


class TestConversationOwnershipEnforced:
    """Test ownership enforcement - users can only access their own conversations."""

    @patch('backend.main.database.get_chat_by_id')
    def test_cannot_access_other_users_conversation(
        self,
        mock_get_chat,
        client_with_mocked_auth,
        mock_auth_user
    ):
        """Test that accessing another user's conversation returns 403."""
        # Arrange
        mock_get_chat.return_value = {
            "id": "other-user-conv",
            "user_id": 999,  # Different user_id
            "created_at": "2024-01-15T10:00:00",
            "title": "Other User's Conversation",
            "type": "council"
        }

        # Act
        response = client_with_mocked_auth.get("/api/conversations/other-user-conv")

        # Assert
        assert response.status_code == 403

    @patch('backend.main.database.delete_chat')
    @patch('backend.main.database.get_chat_by_id')
    def test_cannot_delete_other_users_conversation(
        self,
        mock_get_chat,
        mock_delete_chat,
        client_with_mocked_auth,
        mock_auth_user
    ):
        """Test that deleting another user's conversation returns 403."""
        # Arrange
        mock_get_chat.return_value = {
            "id": "other-user-conv",
            "user_id": 999,
            "created_at": "2024-01-15T10:00:00",
            "title": "Other User's Conversation",
            "type": "council"
        }

        # Act
        response = client_with_mocked_auth.delete("/api/conversations/other-user-conv")

        # Assert
        assert response.status_code == 403
        mock_delete_chat.assert_not_called()


class TestFirstMessageGeneratesTitle:
    """Test that first message triggers title generation."""

    @patch('backend.main.database.create_message')
    @patch('backend.main.database.update_chat_title')
    @patch('backend.main.run_full_council')
    @patch('backend.main.generate_conversation_title')
    @patch('backend.main.database.get_messages_by_chat_id')
    @patch('backend.main.database.get_chat_by_id')
    def test_first_message_generates_title(
        self,
        mock_get_chat,
        mock_get_messages,
        mock_gen_title,
        mock_run_council,
        mock_update_title,
        mock_create_message,
        client_with_mocked_auth,
        mock_auth_user
    ):
        """Test that the first message triggers title generation."""
        # Arrange
        conversation_id = "abc123"

        mock_get_chat.return_value = {
            "id": conversation_id,
            "user_id": mock_auth_user["user_id"],
            "created_at": "2024-01-15T10:00:00",
            "title": "New Conversation",
            "type": "council"
        }
        mock_get_messages.return_value = []  # Empty - first message

        mock_gen_title.return_value = "Generated Title About AI"
        mock_run_council.return_value = (
            [{"model": "test", "response": "test"}],
            [{"model": "test", "ranking": "A"}],
            {"response": "Final answer"},
            {"label_to_model": {}}
        )

        # Act
        response = client_with_mocked_auth.post(
            f"/api/conversations/{conversation_id}/message",
            json={"content": "What is AI?"}
        )

        # Assert
        assert response.status_code == 200
        mock_gen_title.assert_called_once()
        mock_update_title.assert_called_once_with(conversation_id, "Generated Title About AI")

    @patch('backend.main.database.create_message')
    @patch('backend.main.database.update_chat_title')
    @patch('backend.main.run_full_council')
    @patch('backend.main.generate_conversation_title')
    @patch('backend.main.database.get_messages_by_chat_id')
    @patch('backend.main.database.get_chat_by_id')
    def test_subsequent_message_does_not_generate_title(
        self,
        mock_get_chat,
        mock_get_messages,
        mock_gen_title,
        mock_run_council,
        mock_update_title,
        mock_create_message,
        client_with_mocked_auth,
        mock_auth_user
    ):
        """Test that subsequent messages do not trigger title generation."""
        # Arrange
        conversation_id = "abc123"

        mock_get_chat.return_value = {
            "id": conversation_id,
            "user_id": mock_auth_user["user_id"],
            "created_at": "2024-01-15T10:00:00",
            "title": "Existing Title",
            "type": "council"
        }
        mock_get_messages.return_value = [{"role": "user", "content": "previous"}]  # Not empty

        mock_run_council.return_value = (
            [{"model": "test", "response": "test"}],
            [{"model": "test", "ranking": "A"}],
            {"response": "Final answer"},
            {"label_to_model": {}}
        )

        # Act
        response = client_with_mocked_auth.post(
            f"/api/conversations/{conversation_id}/message",
            json={"content": "Follow-up question"}
        )

        # Assert
        assert response.status_code == 200
        mock_gen_title.assert_not_called()
        mock_update_title.assert_not_called()
