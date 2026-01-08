Feature: Main API uses database for persistence
  As a user of the LLM Council
  I want my conversations stored in the database
  So that my chat history persists reliably

  Background:
    Given the system is configured to use database persistence

  Scenario: Create conversation stores to database
    Given a user is authenticated
    When the user creates a new conversation
    Then the conversation is stored in the database
    And the response contains a conversation identifier

  Scenario: Add user message stores with user role
    Given a conversation exists with identifier "abc123"
    And a user is authenticated
    When the user sends a message "Hello" to conversation "abc123"
    Then a message is stored in the database with:
      | field   | value   |
      | role    | user    |
      | content | Hello   |
    And no stage data is stored for the user message

  Scenario: Add assistant message stores stage data separately
    Given a conversation exists with identifier "abc123"
    And the council has generated responses for stages 1, 2, and 3
    When the assistant response is saved to conversation "abc123"
    Then a message is stored in the database with:
      | field   | value     |
      | role    | assistant |
    And the stage 1 responses are stored in the stage1 column
    And the stage 2 rankings are stored in the stage2 column
    And the stage 3 synthesis is stored in the stage3 column
    And the message content contains the final synthesized answer

  Scenario: Get conversation retrieves from database
    Given a conversation exists in the database with identifier "abc123"
    And the conversation has messages
    When the user requests conversation "abc123"
    Then the conversation is retrieved from the database
    And the response uses "id" as the identifier field
    And all messages for the conversation are included
