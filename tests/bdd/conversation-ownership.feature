Feature: Conversation Ownership
  As an authenticated user
  I want my conversations to be private to my account
  So that other users cannot access my chat history

  Background:
    Given I am logged in as a user

  # Ownership Assignment

  Scenario: New conversation is assigned to creating user
    Given I am logged in
    When I create a new conversation
    Then that conversation should be associated with my user account

  # Ownership Validation on Retrieval

  Scenario: Successfully retrieve my own conversation
    Given I have created a conversation
    When I request that conversation
    Then I should receive the conversation details
    And the response should include all messages in that conversation

  Scenario: Cannot retrieve conversation owned by another user
    Given another user has created a conversation
    When I request that conversation
    Then I should receive an access denied response
    And no conversation data should be returned

  Scenario: Cannot list conversations owned by other users
    Given multiple users have created conversations
    When I request my conversation list
    Then I should only see conversations I created
    And the count should match my conversation count

  # Error Cases

  Scenario: Request non-existent conversation returns not found
    Given I am logged in
    When I request a conversation that does not exist
    Then I should receive a not found response

  Scenario: Request conversation without authentication returns unauthorized
    Given I have a conversation
    When I request that conversation without being logged in
    Then I should receive an unauthorized response
