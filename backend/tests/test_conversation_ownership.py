"""
BDD Tests for Conversation Ownership
Tests derived from Gherkin scenarios in prompts/001-bdd-conversation-ownership.md

Feature: Conversation Ownership
  As an authenticated user
  I want my conversations to be private to my account
  So that other users cannot access my chat history
"""

import pytest
from fastapi.testclient import TestClient
from ..main import app
from ..auth import sessions
from .. import storage
from .. import database


client = TestClient(app)


@pytest.fixture
def alice_session():
    """Create session for alice@example.com with real database user."""
    # Create actual user in database
    alice_user = database.upsert_user(
        google_id="alice_google_id",
        email="alice@example.com",
        name="Alice",
        picture_url=None
    )
    if alice_user is None:
        pytest.skip("Database not available")

    session_id = "alice_session_123"
    sessions[session_id] = {
        "email": "alice@example.com",
        "name": "Alice",
        "picture": None,
        "user_id": alice_user["id"],
    }
    yield session_id, sessions[session_id]
    # Cleanup
    if session_id in sessions:
        del sessions[session_id]


@pytest.fixture
def bob_session():
    """Create session for bob@example.com with real database user."""
    # Create actual user in database
    bob_user = database.upsert_user(
        google_id="bob_google_id",
        email="bob@example.com",
        name="Bob",
        picture_url=None
    )
    if bob_user is None:
        pytest.skip("Database not available")

    session_id = "bob_session_456"
    sessions[session_id] = {
        "email": "bob@example.com",
        "name": "Bob",
        "picture": None,
        "user_id": bob_user["id"],
    }
    yield session_id, sessions[session_id]
    # Cleanup
    if session_id in sessions:
        del sessions[session_id]


@pytest.fixture(autouse=True)
def cleanup_conversations():
    """Clean up all conversations after each test"""
    yield
    # Delete all conversation files
    from ..config import DATA_DIR
    from pathlib import Path
    data_path = Path(DATA_DIR)
    if data_path.exists():
        for file in data_path.glob("*.json"):
            file.unlink()


@pytest.mark.unit
def test_new_conversation_assigned_to_creating_user(alice_session):
    """
    Scenario: New conversation is assigned to creating user
      Given I am logged in
      When I create a new conversation
      Then that conversation should be associated with my user account
    """
    session_id, user = alice_session

    # When: Create a new conversation
    response = client.post(
        "/api/conversations",
        cookies={"session_id": session_id}
    )

    # Then: Conversation is created
    assert response.status_code == 200
    data = response.json()
    conversation_id = data["id"]

    # And: Conversation is associated with alice's user account
    conversation = storage.get_conversation(conversation_id)
    assert conversation is not None
    assert conversation["user_id"] == user["user_id"]


@pytest.mark.unit
def test_successfully_retrieve_my_own_conversation(alice_session):
    """
    Scenario: Successfully retrieve my own conversation
      Given I have created a conversation
      When I request that conversation
      Then I should receive the conversation details
      And the response should include all messages in that conversation
    """
    session_id, user = alice_session

    # Given: Alice has created a conversation
    create_response = client.post(
        "/api/conversations",
        cookies={"session_id": session_id}
    )
    conversation_id = create_response.json()["id"]

    # Add a message to the conversation
    client.post(
        f"/api/conversations/{conversation_id}/message",
        json={"content": "Hello world"},
        cookies={"session_id": session_id}
    )

    # When: Alice requests that conversation
    response = client.get(
        f"/api/conversations/{conversation_id}",
        cookies={"session_id": session_id}
    )

    # Then: She receives the conversation details
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == conversation_id

    # And: The response includes the user message and assistant response
    # Note: In test environment, LLM calls fail but system still adds an error response
    assert len(data["messages"]) == 2
    assert data["messages"][0]["role"] == "user"
    assert data["messages"][0]["content"] == "Hello world"
    assert data["messages"][1]["role"] == "assistant"


@pytest.mark.unit
def test_cannot_retrieve_conversation_owned_by_another_user(alice_session, bob_session):
    """
    Scenario: Cannot retrieve conversation owned by another user
      Given another user has created a conversation
      When I request that conversation
      Then I should receive an access denied response
      And no conversation data should be returned
    """
    alice_sid, alice_user = alice_session
    bob_sid, bob_user = bob_session

    # Given: Bob has created a conversation
    create_response = client.post(
        "/api/conversations",
        cookies={"session_id": bob_sid}
    )
    bob_conversation_id = create_response.json()["id"]

    # When: Alice requests Bob's conversation
    response = client.get(
        f"/api/conversations/{bob_conversation_id}",
        cookies={"session_id": alice_sid}
    )

    # Then: She receives an access denied response
    assert response.status_code == 403
    data = response.json()
    assert "access denied" in data["detail"].lower() or "forbidden" in data["detail"].lower()


@pytest.mark.unit
def test_cannot_list_conversations_owned_by_other_users(alice_session, bob_session):
    """
    Scenario: Cannot list conversations owned by other users
      Given multiple users have created conversations
      When I request my conversation list
      Then I should only see conversations I created
      And the count should match my conversation count
    """
    alice_sid, alice_user = alice_session
    bob_sid, bob_user = bob_session

    # Given: Alice creates 2 conversations
    alice_conv1 = client.post("/api/conversations", cookies={"session_id": alice_sid}).json()
    alice_conv2 = client.post("/api/conversations", cookies={"session_id": alice_sid}).json()

    # And: Bob creates 1 conversation
    bob_conv1 = client.post("/api/conversations", cookies={"session_id": bob_sid}).json()

    # When: Alice requests her conversation list
    response = client.get(
        "/api/conversations",
        cookies={"session_id": alice_sid}
    )

    # Then: She only sees her own conversations
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # And: The IDs match Alice's conversations
    conversation_ids = {conv["id"] for conv in data}
    assert alice_conv1["id"] in conversation_ids
    assert alice_conv2["id"] in conversation_ids
    assert bob_conv1["id"] not in conversation_ids


@pytest.mark.unit
def test_request_nonexistent_conversation_returns_not_found(alice_session):
    """
    Scenario: Request non-existent conversation returns not found
      Given I am logged in
      When I request a conversation that does not exist
      Then I should receive a not found response
    """
    session_id, user = alice_session

    # When: Alice requests a conversation that doesn't exist
    response = client.get(
        "/api/conversations/nonexistent-id-12345",
        cookies={"session_id": session_id}
    )

    # Then: She receives a not found response
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


@pytest.mark.unit
def test_request_conversation_without_authentication_returns_unauthorized(alice_session):
    """
    Scenario: Request conversation without authentication returns unauthorized
      Given I have a conversation
      When I request that conversation without being logged in
      Then I should receive an unauthorized response
    """
    session_id, user = alice_session

    # Given: Alice has a conversation
    create_response = client.post(
        "/api/conversations",
        cookies={"session_id": session_id}
    )
    conversation_id = create_response.json()["id"]

    # When: Request that conversation without being logged in (no cookie)
    response = client.get(f"/api/conversations/{conversation_id}")

    # Then: Receive an unauthorized response
    assert response.status_code == 401
    data = response.json()
    assert "not authenticated" in data["detail"].lower() or "unauthorized" in data["detail"].lower()


@pytest.mark.unit
def test_cannot_add_message_to_other_users_conversation(alice_session, bob_session):
    """
    Additional test: Cannot add message to conversation owned by another user
    This covers the POST /api/conversations/{id}/message endpoint
    """
    alice_sid, alice_user = alice_session
    bob_sid, bob_user = bob_session

    # Given: Bob has a conversation
    bob_conv = client.post("/api/conversations", cookies={"session_id": bob_sid}).json()

    # When: Alice tries to add a message to Bob's conversation
    response = client.post(
        f"/api/conversations/{bob_conv['id']}/message",
        json={"content": "Trying to hack in"},
        cookies={"session_id": alice_sid}
    )

    # Then: Access is denied
    assert response.status_code == 403


@pytest.mark.unit
def test_cannot_delete_other_users_conversation(alice_session, bob_session):
    """
    Additional test: Cannot delete conversation owned by another user
    This covers the DELETE /api/conversations/{id} endpoint
    """
    alice_sid, alice_user = alice_session
    bob_sid, bob_user = bob_session

    # Given: Bob has a conversation
    bob_conv = client.post("/api/conversations", cookies={"session_id": bob_sid}).json()

    # When: Alice tries to delete Bob's conversation
    response = client.delete(
        f"/api/conversations/{bob_conv['id']}",
        cookies={"session_id": alice_sid}
    )

    # Then: Access is denied
    assert response.status_code == 403

    # And: Bob's conversation still exists
    verify_response = client.get(
        f"/api/conversations/{bob_conv['id']}",
        cookies={"session_id": bob_sid}
    )
    assert verify_response.status_code == 200
