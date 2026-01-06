"""
BDD Tests for Chats Table Schema
Tests derived from Gherkin scenarios in tests/bdd/chats-table-schema.feature

Feature: Chats Table Schema
  As an authenticated user
  I want my chats to be stored with my user identity
  So that my chats are persisted and isolated from other users
"""

import pytest
from backend.database import (
    create_chat,
    get_chats_by_user_id,
    get_chat_by_id,
    get_user_by_email,
    upsert_user
)


@pytest.fixture
def setup_alice():
    """Given a user 'alice@example.com' exists"""
    user = upsert_user(
        google_id="google_alice_123",
        email="alice@example.com",
        name="Alice",
        picture_url=None
    )
    assert user is not None
    return user


@pytest.fixture
def setup_bob():
    """Given a user 'bob@example.com' exists"""
    user = upsert_user(
        google_id="google_bob_456",
        email="bob@example.com",
        name="Bob",
        picture_url=None
    )
    assert user is not None
    return user


@pytest.mark.unit
def test_user_creates_chat_and_retrieves_it(setup_alice):
    """
    Scenario: User creates a chat and retrieves it
    Given a user "alice@example.com" exists
    When alice creates a new chat
    And alice fetches her chat list
    Then the chat list contains the newly created chat
    And the chat belongs to alice
    And the chat has a unique identifier
    And the chat has a creation timestamp
    """
    alice = setup_alice

    # When alice creates a new chat
    created_chat = create_chat(user_id=alice['id'])
    assert created_chat is not None, "Chat creation should succeed"

    # And alice fetches her chat list
    chat_list = get_chats_by_user_id(user_id=alice['id'])

    # Then the chat list contains the newly created chat
    assert len(chat_list) > 0, "Chat list should not be empty"
    chat_ids = [chat['id'] for chat in chat_list]
    assert created_chat['id'] in chat_ids, "Created chat should be in list"

    # And the chat belongs to alice
    found_chat = next((c for c in chat_list if c['id'] == created_chat['id']), None)
    assert found_chat is not None
    assert found_chat['user_id'] == alice['id'], "Chat should belong to alice"

    # And the chat has a unique identifier
    assert 'id' in created_chat
    assert created_chat['id'] is not None
    assert len(str(created_chat['id'])) > 0, "Chat ID should be non-empty"

    # And the chat has a creation timestamp
    assert 'created_at' in created_chat
    assert created_chat['created_at'] is not None


@pytest.mark.unit
def test_user_cannot_see_another_users_chats(setup_alice, setup_bob):
    """
    Scenario: User cannot see another user's chats
    Given a user "alice@example.com" exists
    And a user "bob@example.com" exists
    And alice has created a chat
    When bob fetches his chat list
    Then bob's chat list does not contain alice's chat
    """
    alice = setup_alice
    bob = setup_bob

    # And alice has created a chat
    alice_chat = create_chat(user_id=alice['id'])
    assert alice_chat is not None

    # When bob fetches his chat list
    bob_chat_list = get_chats_by_user_id(user_id=bob['id'])

    # Then bob's chat list does not contain alice's chat
    bob_chat_ids = [chat['id'] for chat in bob_chat_list]
    assert alice_chat['id'] not in bob_chat_ids, "Bob should not see Alice's chat"


@pytest.mark.unit
def test_user_retrieves_their_filtered_chat_list(setup_alice):
    """
    Scenario: User retrieves their filtered chat list
    Given a user "alice@example.com" exists
    And alice has created 2 chats
    When alice fetches her chat list
    Then the chat list contains exactly 2 chats
    And all chats in the list belong to alice
    """
    alice = setup_alice

    # And alice has created 2 chats
    chat1 = create_chat(user_id=alice['id'])
    chat2 = create_chat(user_id=alice['id'])
    assert chat1 is not None
    assert chat2 is not None

    # When alice fetches her chat list
    alice_chat_list = get_chats_by_user_id(user_id=alice['id'])

    # Then the chat list contains exactly 2 chats
    assert len(alice_chat_list) == 2, f"Expected 2 chats, got {len(alice_chat_list)}"

    # And all chats in the list belong to alice
    for chat in alice_chat_list:
        assert chat['user_id'] == alice['id'], f"Chat {chat['id']} should belong to alice"


@pytest.mark.unit
def test_get_chat_by_id_returns_correct_chat(setup_alice):
    """
    Edge case: Verify get_chat_by_id returns the correct chat
    """
    alice = setup_alice

    # Create a chat
    created_chat = create_chat(user_id=alice['id'])
    assert created_chat is not None

    # Retrieve by ID
    retrieved_chat = get_chat_by_id(chat_id=created_chat['id'])

    # Verify it's the same chat
    assert retrieved_chat is not None
    assert retrieved_chat['id'] == created_chat['id']
    assert retrieved_chat['user_id'] == alice['id']


@pytest.mark.unit
def test_empty_chat_list_for_user_with_no_chats(setup_alice):
    """
    Edge case: User with no chats should get empty list
    """
    alice = setup_alice

    # Fetch chat list without creating any chats
    chat_list = get_chats_by_user_id(user_id=alice['id'])

    # Should return empty list, not None
    assert chat_list is not None
    assert isinstance(chat_list, list)
    assert len(chat_list) == 0, "New user should have empty chat list"


@pytest.mark.unit
def test_get_chat_by_id_returns_none_for_nonexistent_chat():
    """
    Edge case: get_chat_by_id should return None for non-existent chat
    """
    # Try to get a chat that doesn't exist
    non_existent_id = "00000000-0000-0000-0000-000000000000"
    result = get_chat_by_id(chat_id=non_existent_id)

    assert result is None, "Should return None for non-existent chat"
