Feature: Messages Table Schema
  As an authenticated user
  I want my messages to be stored with chat association and stage data
  So that my queries and LLM responses are persisted and retrievable

  Background:
    Given the database is available
    And a user "alice@example.com" exists
    And alice has created a chat

  # User Message Storage

  Scenario: User message is stored and retrieved with content
    When alice creates a user message with content "What is machine learning?"
    And alice fetches messages for the chat
    Then the messages contain a user message
    And the user message content equals "What is machine learning?"
    And the user message has a creation timestamp
    And the user message belongs to alice's chat

  # Assistant Message with Stage Data

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

  # Chronological Order

  Scenario: Messages are retrieved in chronological order
    Given alice has created 3 messages in the chat over time
    When alice fetches messages for the chat
    Then the messages are returned in chronological order
    And the first message was created before the second message
    And the second message was created before the third message

  # Single Message Retrieval

  Scenario: Single message is retrieved by ID with stage data
    Given alice has created an assistant message with stage data
    When alice fetches the message by its ID
    Then the message is returned
    And the message has stage 1 data with model responses
    And the message has stage 2 data with rankings
    And the message has stage 3 data with synthesis

  # Cascade Delete

  Scenario: Messages are deleted when parent chat is deleted
    Given alice has created 2 messages in the chat
    When alice deletes the chat
    Then the chat no longer exists
    And the messages associated with the chat are also deleted
