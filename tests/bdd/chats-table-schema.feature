Feature: Chats Table Schema
  As an authenticated user
  I want my chats to be stored with my user identity
  So that my chats are persisted and isolated from other users

  Background:
    Given the database is available

  # Happy Path: Create and Retrieve

  Scenario: User creates a chat and retrieves it
    Given a user "alice@example.com" exists
    When alice creates a new chat
    And alice fetches her chat list
    Then the chat list contains the newly created chat
    And the chat belongs to alice
    And the chat has a unique identifier
    And the chat has a creation timestamp

  # User Isolation

  Scenario: User cannot see another user's chats
    Given a user "alice@example.com" exists
    And a user "bob@example.com" exists
    And alice has created a chat
    When bob fetches his chat list
    Then bob's chat list does not contain alice's chat

  # Chat List Retrieval

  Scenario: User retrieves their filtered chat list
    Given a user "alice@example.com" exists
    And alice has created 2 chats
    When alice fetches her chat list
    Then the chat list contains exactly 2 chats
    And all chats in the list belong to alice
