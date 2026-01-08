Feature: Chat Storage Messages
  As a user of the LLM Council application
  I want to store and retrieve messages in my chats
  So that my conversation history is preserved

  Background:
    Given a registered user exists in the system
    And the user has an existing chat

  Scenario: User message is added to chat
    When the user adds a message with content "Hello, council"
    Then the message should be saved to the chat
    And the message role should be "user"
    And the message content should be "Hello, council"

  Scenario: Assistant message with stage data is added to chat
    Given the user has sent a message
    When the assistant responds with stage one, stage two, and stage three data
    Then the assistant message should be saved to the chat
    And the message role should be "assistant"
    And the stage one data should be preserved
    And the stage two data should be preserved
    And the stage three data should be preserved

  Scenario: User retrieves all messages from a chat
    Given the chat has multiple messages
    When the user requests all messages from the chat
    Then all messages should be returned
    And the messages should be in chronological order

  Scenario: User retrieves messages from empty chat
    Given the chat has no messages
    When the user requests all messages from the chat
    Then an empty list should be returned

  Scenario: Adding message to non-existent chat fails
    When the user attempts to add a message to a non-existent chat
    Then the message should not be added
    And the operation should return a failure indicator
