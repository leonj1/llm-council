Feature: Chat Storage Retrieval
  As a user of the LLM Council application
  I want to retrieve my stored chats
  So that I can continue previous conversations

  Background:
    Given a registered user exists in the system
    And the user has existing chats in storage

  Scenario: User retrieves their own chat by identifier
    When the user requests a chat by its identifier
    Then the chat should be returned
    And the chat should include the user association
    And the chat should include the creation timestamp

  Scenario: User retrieves a chat that does not exist
    When the user requests a chat with a non-existent identifier
    Then no chat should be returned

  Scenario: User lists all their chats
    Given the user has multiple chats
    When the user requests a list of their chats
    Then all chats belonging to the user should be returned
    And each chat should include the title
    And each chat should include the type
    And each chat should include the message count
    And the chats should be ordered by creation time with newest first

  Scenario: User with no chats lists their chats
    Given the user has no chats
    When the user requests a list of their chats
    Then an empty list should be returned
