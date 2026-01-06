Feature: Chat URL Routing
  As an authenticated user
  I want the URL to reflect the currently selected chat
  So that I can bookmark, share, and navigate directly to specific conversations

  Background:
    Given I am logged in as a user

  # Happy Paths - URL Navigation

  Scenario: URL updates when selecting a chat from sidebar
    Given I have a conversation in my chat history
    When I select that conversation from the sidebar
    Then the URL should update to include the conversation identifier
    And the selected conversation should display

  Scenario: Navigate directly to a chat via URL
    Given I have an existing conversation
    When I navigate directly to the URL for that conversation
    Then that conversation should load and display
    And the sidebar should highlight that conversation

  Scenario: Create new conversation updates URL
    Given I am on the chat page
    When I create a new conversation
    Then the URL should update to include the new conversation identifier
    And a blank conversation should display

  Scenario: Browser back button navigates chat history
    Given I have selected multiple conversations in sequence
    When I press the browser back button
    Then the previously selected conversation should display
    And the URL should reflect the previous conversation

  Scenario: Browser forward button navigates chat history
    Given I have used the back button to return to a previous conversation
    When I press the browser forward button
    Then the next conversation in history should display
    And the URL should reflect that conversation

  # Edge Cases

  Scenario: Navigate to base chat URL with no conversation selected
    Given I have conversations in my history
    When I navigate to the base chat URL without a conversation identifier
    Then no conversation should be selected
    And the sidebar should display my conversation list

  Scenario: Navigate to URL for non-existent conversation
    Given I am logged in
    When I navigate to a URL with a conversation identifier that does not exist
    Then I should be redirected to the base chat page
    And I should see a message indicating the conversation was not found

  Scenario: Conversation list filtered to current user only
    Given there are conversations belonging to multiple users in the system
    When I view my conversation list
    Then I should only see conversations that belong to me
    And I should not see conversations belonging to other users

  # Authentication and Authorization

  Scenario: Access denied when viewing another user's conversation
    Given another user has a conversation
    When I attempt to navigate to the URL for that conversation
    Then I should be redirected to the base chat page
    And I should see a message indicating access is denied

  Scenario: Unauthenticated user redirected from chat URL
    Given I am not logged in
    When I navigate to a chat URL with a conversation identifier
    Then I should be redirected to the landing page
    And I should be prompted to log in

  Scenario: Unauthenticated user redirected from base chat page
    Given I am not logged in
    When I navigate to the base chat page
    Then I should be redirected to the landing page
