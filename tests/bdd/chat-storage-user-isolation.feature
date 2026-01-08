Feature: Chat Storage User Isolation
  As a user of the LLM Council application
  I want my chats to be private and isolated from other users
  So that my conversations remain confidential

  Background:
    Given two different users exist in the system
    And user one has created a chat

  Scenario: User cannot retrieve another user's chat
    When user two requests user one's chat by identifier
    Then no chat should be returned
    And the request should be treated as if the chat does not exist

  Scenario: User cannot see another user's chats in their list
    Given user two also has their own chats
    When user two requests a list of their chats
    Then only chats belonging to user two should be returned
    And user one's chats should not appear in the list

  Scenario: User cannot add messages to another user's chat
    When user two attempts to add a message to user one's chat
    Then the message should not be added
    And the operation should fail with an authorization error

  Scenario: User cannot delete another user's chat
    When user two attempts to delete user one's chat
    Then the chat should not be deleted
    And the operation should return a failure indicator
