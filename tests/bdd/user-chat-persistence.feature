Feature: User Chat Persistence
  As an authenticated user
  I want my chats and LLM responses to be persisted in the database
  So that I can access my conversation history across sessions and devices

  Background:
    Given the application is running
    And the database is available

  # Chat Creation and Retrieval

  Scenario: User creates a chat and retrieves it from the database
    Given a user is authenticated with email "alice@example.com"
    When the user creates a new chat
    And the user fetches their chat list from the database
    Then the fetched chat list contains the newly created chat
    And the fetched chat has the user ID matching "alice@example.com"
    And the fetched chat has a unique identifier
    And the fetched chat has a creation timestamp

  Scenario: User's chat is not returned when another user queries the database
    Given a user "alice@example.com" has created a chat
    When user "bob@example.com" fetches their chat list from the database
    Then the fetched chat list does not contain chats from "alice@example.com"

  # Query Submission and Retrieval

  Scenario: User submits a query and retrieves it from the database
    Given a user is authenticated with email "alice@example.com"
    And the user has created a chat
    When the user submits a query "What is the meaning of life?"
    And the user fetches the chat messages from the database
    Then the fetched messages contain a user message
    And the fetched user message content equals "What is the meaning of life?"
    And the fetched user message has a timestamp

  # LLM Response Retrieval

  Scenario: Stage 1 LLM responses are retrieved from the database
    Given a user is authenticated with email "alice@example.com"
    And the user has created a chat
    When the user submits a query "Explain quantum computing"
    And the council models respond with Stage 1 responses
    And the user fetches the chat messages from the database
    Then the fetched assistant message contains Stage 1 data
    And the fetched Stage 1 data contains responses from multiple models
    And each fetched Stage 1 response has a model identifier
    And each fetched Stage 1 response has response content

  Scenario: Stage 2 rankings are retrieved from the database
    Given a user is authenticated with email "alice@example.com"
    And the user has created a chat
    When the user submits a query "Explain quantum computing"
    And the council completes Stage 2 rankings
    And the user fetches the chat messages from the database
    Then the fetched assistant message contains Stage 2 data
    And the fetched Stage 2 data contains rankings from multiple models
    And each fetched Stage 2 ranking has an evaluating model
    And each fetched Stage 2 ranking has a parsed ranking order

  Scenario: Stage 3 synthesis is retrieved from the database
    Given a user is authenticated with email "alice@example.com"
    And the user has created a chat
    When the user submits a query "Explain quantum computing"
    And the chairman model synthesizes the final response
    And the user fetches the chat messages from the database
    Then the fetched assistant message contains Stage 3 data
    And the fetched Stage 3 data has the chairman model identifier
    And the fetched Stage 3 data has the synthesized response content

  # Complete Conversation Retrieval

  Scenario: Multiple exchanges are retrieved from the database in order
    Given a user is authenticated with email "alice@example.com"
    And the user has created a chat
    When the user submits a query "What is machine learning?"
    And the council processes the query through all stages
    And the user submits a follow-up query "How does it differ from deep learning?"
    And the council processes the follow-up through all stages
    And the user fetches the chat messages from the database
    Then the fetched messages contain exactly 4 messages
    And the fetched message at index 0 is a user message with content "What is machine learning?"
    And the fetched message at index 1 is an assistant message with Stage 1, Stage 2, and Stage 3 data
    And the fetched message at index 2 is a user message with content "How does it differ from deep learning?"
    And the fetched message at index 3 is an assistant message with Stage 1, Stage 2, and Stage 3 data

  # Chat List Retrieval

  Scenario: User retrieves all their chats with metadata from the database
    Given a user is authenticated with email "alice@example.com"
    And the user has created 3 chats with conversations
    When the user fetches their chat list from the database
    Then the fetched chat list contains exactly 3 chats
    And each fetched chat has a title
    And each fetched chat has a creation timestamp
    And each fetched chat has a message count
    And all fetched chats belong to user "alice@example.com"

  Scenario: New user has empty chat list
    Given a user is authenticated with email "newuser@example.com"
    And the user has not created any chats
    When the user fetches their chat list from the database
    Then the fetched chat list is empty
    And no error is returned

  # Chat Management

  Scenario: User deletes their own chat
    Given a user is authenticated with email "alice@example.com"
    And the user has created a chat with messages
    When the user deletes the chat
    And the user fetches their chat list from the database
    Then the fetched chat list does not contain the deleted chat
    And the deleted chat messages are also removed

  Scenario: User cannot delete another user's chat
    Given user "alice@example.com" has created a chat with id "chat-456"
    When user "bob@example.com" attempts to delete chat "chat-456"
    Then the response is a forbidden error
    And the chat remains in the database for "alice@example.com"

  # Session Persistence Verification

  Scenario: User retrieves same chat data after re-authentication
    Given a user is authenticated with email "alice@example.com"
    And the user has created a chat with a query "Test persistence query"
    And the council has responded with all stages
    When the user session ends
    And the user authenticates again with email "alice@example.com"
    And the user fetches their chat list from the database
    And the user fetches the chat messages from the database
    Then the fetched user message content equals "Test persistence query"
    And the fetched assistant message contains Stage 1, Stage 2, and Stage 3 data

  # Authorization - Data Isolation

  Scenario: Unauthenticated request returns no user chats
    Given a user is not authenticated
    When an unauthenticated request fetches chats from the database
    Then the response is an authentication error
    And no chat data is returned

  Scenario: User cannot fetch another user's chat data by ID
    Given user "alice@example.com" has created a chat with id "chat-123"
    And user "alice@example.com" has submitted a query "Alice's private question"
    When user "bob@example.com" attempts to fetch chat "chat-123" from the database
    Then the response is a forbidden error
    And no chat messages are returned
    And "Alice's private question" is not exposed to "bob@example.com"
