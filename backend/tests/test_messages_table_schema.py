"""
BDD Tests for Messages Table Schema
Tests derived from Gherkin scenarios in tests/bdd/messages-table-schema.feature

Feature: Messages Table Schema
  As an authenticated user
  I want my messages to be stored with chat association and stage data
  So that my queries and LLM responses are persisted and retrievable
"""

import pytest
import time
import json
from backend.database import (
    create_message,
    get_messages_by_chat_id,
    get_message_by_id,
    delete_chat,
    create_chat,
    get_chat_by_id,
    get_user_by_email,
    upsert_user
)


@pytest.fixture
def setup_alice_with_chat():
    """
    Background:
    Given the database is available
    And a user "alice@example.com" exists
    And alice has created a chat
    """
    # Given a user "alice@example.com" exists
    user = upsert_user(
        google_id="google_alice_messages_123",
        email="alice@example.com",
        name="Alice",
        picture_url=None
    )
    assert user is not None

    # And alice has created a chat
    chat = create_chat(user_id=user['id'])
    assert chat is not None

    return {'user': user, 'chat': chat}


@pytest.mark.unit
def test_user_message_is_stored_and_retrieved_with_content(setup_alice_with_chat):
    """
    Scenario: User message is stored and retrieved with content
    When alice creates a user message with content "What is machine learning?"
    And alice fetches messages for the chat
    Then the messages contain a user message
    And the user message content equals "What is machine learning?"
    And the user message has a creation timestamp
    And the user message belongs to alice's chat
    """
    alice = setup_alice_with_chat
    chat_id = alice['chat']['id']

    # When alice creates a user message with content "What is machine learning?"
    created_message = create_message(
        chat_id=chat_id,
        role='user',
        content='What is machine learning?',
        stage1_data=None,
        stage2_data=None,
        stage3_data=None
    )
    assert created_message is not None, "Message creation should succeed"

    # And alice fetches messages for the chat
    messages = get_messages_by_chat_id(chat_id=chat_id)

    # Then the messages contain a user message
    assert len(messages) > 0, "Messages list should not be empty"
    user_messages = [m for m in messages if m['role'] == 'user']
    assert len(user_messages) > 0, "Should have at least one user message"

    # And the user message content equals "What is machine learning?"
    user_message = user_messages[0]
    assert user_message['content'] == 'What is machine learning?', "Content should match"

    # And the user message has a creation timestamp
    assert 'created_at' in user_message
    assert user_message['created_at'] is not None

    # And the user message belongs to alice's chat
    assert user_message['chat_id'] == chat_id


@pytest.mark.unit
def test_assistant_message_is_stored_with_stage_data_and_retrieved(setup_alice_with_chat):
    """
    Scenario: Assistant message is stored with Stage 1, 2, 3 data and retrieved
    When alice creates an assistant message with stage data
    And the stage 1 data contains model responses
    And the stage 2 data contains rankings
    And the stage 3 data contains the synthesis
    And alice fetches messages for the chat
    Then the messages contain an assistant message
    And the assistant message has stage 1 data with model responses
    And the assistant message has stage 2 data with rankings
    And the assistant message has stage 3 data with synthesis
    """
    alice = setup_alice_with_chat
    chat_id = alice['chat']['id']

    # When alice creates an assistant message with stage data
    # And the stage 1 data contains model responses
    stage1_data = {
        'responses': [
            {'model': 'openai/gpt-4', 'content': 'Response 1'},
            {'model': 'anthropic/claude-3', 'content': 'Response 2'}
        ]
    }

    # And the stage 2 data contains rankings
    stage2_data = {
        'rankings': [
            {'rank': 1, 'response': 'Response A'},
            {'rank': 2, 'response': 'Response B'}
        ]
    }

    # And the stage 3 data contains the synthesis
    stage3_data = {
        'synthesis': 'Final synthesized answer'
    }

    created_message = create_message(
        chat_id=chat_id,
        role='assistant',
        content='Combined response',
        stage1_data=stage1_data,
        stage2_data=stage2_data,
        stage3_data=stage3_data
    )
    assert created_message is not None, "Assistant message creation should succeed"

    # And alice fetches messages for the chat
    messages = get_messages_by_chat_id(chat_id=chat_id)

    # Then the messages contain an assistant message
    assistant_messages = [m for m in messages if m['role'] == 'assistant']
    assert len(assistant_messages) > 0, "Should have at least one assistant message"

    assistant_message = assistant_messages[0]

    # And the assistant message has stage 1 data with model responses
    assert assistant_message['stage1_data'] is not None
    assert 'responses' in assistant_message['stage1_data']
    assert len(assistant_message['stage1_data']['responses']) == 2

    # And the assistant message has stage 2 data with rankings
    assert assistant_message['stage2_data'] is not None
    assert 'rankings' in assistant_message['stage2_data']
    assert len(assistant_message['stage2_data']['rankings']) == 2

    # And the assistant message has stage 3 data with synthesis
    assert assistant_message['stage3_data'] is not None
    assert 'synthesis' in assistant_message['stage3_data']
    assert assistant_message['stage3_data']['synthesis'] == 'Final synthesized answer'


@pytest.mark.unit
def test_messages_are_retrieved_in_chronological_order(setup_alice_with_chat):
    """
    Scenario: Messages are retrieved in chronological order
    Given alice has created 3 messages in the chat over time
    When alice fetches messages for the chat
    Then the messages are returned in chronological order
    And the first message was created before the second message
    And the second message was created before the third message
    """
    alice = setup_alice_with_chat
    chat_id = alice['chat']['id']

    # Given alice has created 3 messages in the chat over time
    message1 = create_message(
        chat_id=chat_id,
        role='user',
        content='First message',
        stage1_data=None,
        stage2_data=None,
        stage3_data=None
    )
    assert message1 is not None
    time.sleep(0.01)  # Small delay to ensure different timestamps

    message2 = create_message(
        chat_id=chat_id,
        role='assistant',
        content='Second message',
        stage1_data=None,
        stage2_data=None,
        stage3_data=None
    )
    assert message2 is not None
    time.sleep(0.01)

    message3 = create_message(
        chat_id=chat_id,
        role='user',
        content='Third message',
        stage1_data=None,
        stage2_data=None,
        stage3_data=None
    )
    assert message3 is not None

    # When alice fetches messages for the chat
    messages = get_messages_by_chat_id(chat_id=chat_id)

    # Then the messages are returned in chronological order
    assert len(messages) == 3, f"Expected 3 messages, got {len(messages)}"

    # And the first message was created before the second message
    assert messages[0]['created_at'] <= messages[1]['created_at']
    assert messages[0]['content'] == 'First message'

    # And the second message was created before the third message
    assert messages[1]['created_at'] <= messages[2]['created_at']
    assert messages[1]['content'] == 'Second message'
    assert messages[2]['content'] == 'Third message'


@pytest.mark.unit
def test_single_message_is_retrieved_by_id_with_stage_data(setup_alice_with_chat):
    """
    Scenario: Single message is retrieved by ID with stage data
    Given alice has created an assistant message with stage data
    When alice fetches the message by its ID
    Then the message is returned
    And the message has stage 1 data with model responses
    And the message has stage 2 data with rankings
    And the message has stage 3 data with synthesis
    """
    alice = setup_alice_with_chat
    chat_id = alice['chat']['id']

    # Given alice has created an assistant message with stage data
    stage1_data = {'responses': [{'model': 'test', 'content': 'test'}]}
    stage2_data = {'rankings': [{'rank': 1}]}
    stage3_data = {'synthesis': 'test synthesis'}

    created_message = create_message(
        chat_id=chat_id,
        role='assistant',
        content='Message with stage data',
        stage1_data=stage1_data,
        stage2_data=stage2_data,
        stage3_data=stage3_data
    )
    assert created_message is not None
    message_id = created_message['id']

    # When alice fetches the message by its ID
    retrieved_message = get_message_by_id(message_id=message_id)

    # Then the message is returned
    assert retrieved_message is not None
    assert retrieved_message['id'] == message_id

    # And the message has stage 1 data with model responses
    assert retrieved_message['stage1_data'] is not None
    assert 'responses' in retrieved_message['stage1_data']

    # And the message has stage 2 data with rankings
    assert retrieved_message['stage2_data'] is not None
    assert 'rankings' in retrieved_message['stage2_data']

    # And the message has stage 3 data with synthesis
    assert retrieved_message['stage3_data'] is not None
    assert retrieved_message['stage3_data']['synthesis'] == 'test synthesis'


@pytest.mark.unit
def test_messages_are_deleted_when_parent_chat_is_deleted(setup_alice_with_chat):
    """
    Scenario: Messages are deleted when parent chat is deleted
    Given alice has created 2 messages in the chat
    When alice deletes the chat
    Then the chat no longer exists
    And the messages associated with the chat are also deleted
    """
    alice = setup_alice_with_chat
    chat_id = alice['chat']['id']

    # Given alice has created 2 messages in the chat
    message1 = create_message(
        chat_id=chat_id,
        role='user',
        content='Message 1',
        stage1_data=None,
        stage2_data=None,
        stage3_data=None
    )
    message2 = create_message(
        chat_id=chat_id,
        role='assistant',
        content='Message 2',
        stage1_data=None,
        stage2_data=None,
        stage3_data=None
    )
    assert message1 is not None
    assert message2 is not None

    # Verify messages exist before deletion
    messages_before = get_messages_by_chat_id(chat_id=chat_id)
    assert len(messages_before) == 2

    # When alice deletes the chat
    delete_result = delete_chat(chat_id=chat_id)
    assert delete_result is True, "Chat deletion should succeed"

    # Then the chat no longer exists
    deleted_chat = get_chat_by_id(chat_id=chat_id)
    assert deleted_chat is None, "Chat should not exist after deletion"

    # And the messages associated with the chat are also deleted
    messages_after = get_messages_by_chat_id(chat_id=chat_id)
    assert len(messages_after) == 0, "Messages should be cascade-deleted with chat"


@pytest.mark.unit
def test_get_messages_returns_empty_list_for_chat_with_no_messages(setup_alice_with_chat):
    """
    Edge case: get_messages_by_chat_id should return empty list for chat with no messages
    """
    alice = setup_alice_with_chat
    chat_id = alice['chat']['id']

    # Fetch messages without creating any
    messages = get_messages_by_chat_id(chat_id=chat_id)

    # Should return empty list, not None
    assert messages is not None
    assert isinstance(messages, list)
    assert len(messages) == 0


@pytest.mark.unit
def test_get_message_by_id_returns_none_for_nonexistent_message():
    """
    Edge case: get_message_by_id should return None for non-existent message
    """
    # Try to get a message that doesn't exist
    non_existent_id = 999999
    result = get_message_by_id(message_id=non_existent_id)

    assert result is None, "Should return None for non-existent message"


@pytest.mark.unit
def test_user_message_has_null_stage_data(setup_alice_with_chat):
    """
    Edge case: User messages should have NULL stage data
    """
    alice = setup_alice_with_chat
    chat_id = alice['chat']['id']

    # Create user message with explicit None stage data
    created_message = create_message(
        chat_id=chat_id,
        role='user',
        content='User question',
        stage1_data=None,
        stage2_data=None,
        stage3_data=None
    )
    assert created_message is not None

    # Retrieve and verify stage data is None
    retrieved = get_message_by_id(message_id=created_message['id'])
    assert retrieved['stage1_data'] is None
    assert retrieved['stage2_data'] is None
    assert retrieved['stage3_data'] is None
