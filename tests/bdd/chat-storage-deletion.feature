Feature: Chat Storage Deletion
  As a user of the LLM Council application
  I want to delete my chats
  So that I can manage my conversation history

  Background:
    Given a registered user exists in the system
    And the user has an existing chat with messages

  Scenario: User deletes their own chat
    When the user deletes their chat
    Then the chat should be removed from storage
    And all messages in the chat should be removed
    And the operation should return a success indicator

  Scenario: User attempts to delete a non-existent chat
    When the user attempts to delete a chat that does not exist
    Then the operation should return a failure indicator

  Scenario: Deleted chat is no longer retrievable
    When the user deletes their chat
    And the user attempts to retrieve the deleted chat
    Then no chat should be returned

  Scenario: Deleted chat no longer appears in chat list
    When the user deletes their chat
    And the user requests a list of their chats
    Then the deleted chat should not appear in the list
