Feature: Chat Storage Creation
  As a user of the LLM Council application
  I want my chats to be created and stored persistently
  So that I can access them across sessions

  Background:
    Given a registered user exists in the system

  Scenario: User creates a new chat successfully
    When the user creates a new chat
    Then the chat should be saved to persistent storage
    And the chat should be associated with the user
    And the chat should have a unique identifier
    And the chat should have a default title of "New Conversation"

  Scenario: User creates a council-type chat
    When the user creates a chat of type "council"
    Then the chat type should be "council"
    And the chat should be saved to persistent storage

  Scenario: User creates a movie script chat
    When the user creates a chat of type "movie_script"
    Then the chat type should be "movie_script"
    And the chat should be saved to persistent storage

  Scenario: Chat creation fails when storage is unavailable
    Given the storage system is unavailable
    When the user attempts to create a chat
    Then no chat should be created
    And the operation should return a failure indicator
