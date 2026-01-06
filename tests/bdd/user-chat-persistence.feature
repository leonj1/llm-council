Feature: User Chat Persistence
  As an authenticated user
  I want my chats and LLM responses to be persisted in the database
  So that I can access my conversation history across sessions and devices

  Background:
    Given the application is running
    And the database is available

  # Chat Creation and Ownership

  Scenario: Authenticated user creates a chat that is assigned to them
    Given a user is authenticated with email "alice@example.com"
    When the user creates a new chat
    Then the chat is persisted in the database
    And the chat is assigned to user "alice@example.com"
    And the chat has a unique identifier
    And the chat has a creation timestamp

  Scenario: Chat is only visible to the user who created it
    Given a user is authenticated with email "alice@example.com"
    And the user has created a chat
    When a different user with email "bob@example.com" lists their chats
    Then the chat created by "alice@example.com" is not visible to "bob@example.com"

  # Query Submission and Persistence

  Scenario: User submits a query and it is persisted
    Given a user is authenticated with email "alice@example.com"
    And the user has created a chat
    When the user submits a query "What is the meaning of life?"
    Then the query is persisted in the database
    And the query is associated with the chat
    And the query has a timestamp
    And the query content matches "What is the meaning of life?"

  # LLM Response Persistence

  Scenario: LLM responses from Stage 1 are persisted
    Given a user is authenticated with email "alice@example.com"
    And the user has created a chat
    When the user submits a query "Explain quantum computing"
    And the council models respond with Stage 1 responses
    Then all Stage 1 responses are persisted in the database
    And each Stage 1 response includes the model identifier
    And each Stage 1 response includes the response content

  Scenario: LLM rankings from Stage 2 are persisted
    Given a user is authenticated with email "alice@example.com"
    And the user has created a chat
    When the user submits a query "Explain quantum computing"
    And the council completes Stage 2 rankings
    Then all Stage 2 rankings are persisted in the database
    And each ranking includes the evaluating model
    And each ranking includes the parsed ranking order

  Scenario: Final synthesis from Stage 3 is persisted
    Given a user is authenticated with email "alice@example.com"
    And the user has created a chat
    When the user submits a query "Explain quantum computing"
    And the chairman model synthesizes the final response
    Then the Stage 3 response is persisted in the database
    And the response includes the chairman model identifier
    And the response includes the synthesized content

  # Full Conversation Flow

  Scenario: Complete conversation with multiple exchanges is persisted
    Given a user is authenticated with email "alice@example.com"
    And the user has created a chat
    When the user submits a query "What is machine learning?"
    And the council processes the query through all stages
    And the user submits a follow-up query "How does it differ from deep learning?"
    And the council processes the follow-up through all stages
    Then the chat contains two user messages
    And the chat contains two assistant responses
    And each assistant response has Stage 1, Stage 2, and Stage 3 data
    And all data is persisted in the database

  # Data Retrieval

  Scenario: User can retrieve their chat history
    Given a user is authenticated with email "alice@example.com"
    And the user has multiple chats with conversations
    When the user requests their chat list
    Then all chats belonging to the user are returned
    And each chat includes its title
    And each chat includes its creation timestamp
    And each chat includes the message count

  Scenario: User can retrieve full conversation from a chat
    Given a user is authenticated with email "alice@example.com"
    And the user has a chat with completed conversations
    When the user requests the full chat details
    Then all messages in the chat are returned
    And user messages include the query content
    And assistant messages include all stage data
    And the conversation order is preserved

  # Session Continuity

  Scenario: User chats persist across sessions
    Given a user is authenticated with email "alice@example.com"
    And the user has created chats and conversations
    When the user logs out
    And the user logs back in with email "alice@example.com"
    Then the user can access all their previous chats
    And all conversation data is intact

  # Authorization

  Scenario: Unauthenticated user cannot create chats
    Given a user is not authenticated
    When the user attempts to create a chat
    Then the request is rejected with an authentication error
    And no chat is created in the database

  Scenario: User cannot access another user's chat by ID
    Given a user is authenticated with email "alice@example.com"
    And "alice@example.com" has created a chat with id "chat-123"
    When a user authenticated as "bob@example.com" attempts to access "chat-123"
    Then the request is rejected with a forbidden error
    And the chat data is not returned
