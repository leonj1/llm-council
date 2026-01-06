---
executor: bdd
source_feature: ./tests/bdd/chats-table-schema.feature
---

<objective>
Implement the Chats Table Schema feature as defined by the BDD scenarios below.
Create a Flyway migration for the chats table with user_id foreign key, and repository functions in database.py.
The implementation must make all Gherkin scenarios pass.
</objective>

<gherkin>
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
</gherkin>

<requirements>
Based on the Gherkin scenarios, implement:

1. Flyway migration V2 for chats table (`sql/V2__create_chats_table.sql`)
   - id: VARCHAR(36) PRIMARY KEY (UUID)
   - user_id: INT NOT NULL with foreign key to users(id)
   - created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   - Index on user_id for efficient queries

2. Repository function: `create_chat(user_id: int) -> Optional[dict]`
   - Generate UUID for chat id
   - Insert into chats table
   - Return created chat record

3. Repository function: `get_chats_by_user_id(user_id: int) -> List[dict]`
   - Return all chats for the given user
   - Filter by user_id (user isolation)

4. Repository function: `get_chat_by_id(chat_id: str) -> Optional[dict]`
   - Return single chat by id

Edge Cases to Handle:
- Database unavailable (return None/empty list)
- Non-existent user_id (foreign key constraint)
- Empty chat list for user with no chats
</requirements>

<context>
BDD Specification: specs/BDD-SPEC-chats-table-schema.md
Gap Analysis: specs/GAP-ANALYSIS.md

Reuse Opportunities (from gap analysis):
- `get_db_cursor()` context manager from database.py
- `get_user_by_email()` for test setup
- Pattern: Functions return Optional[dict] with dictionary cursor
- Pattern: InnoDB engine, utf8mb4 charset for migrations

New Components Needed:
- sql/V2__create_chats_table.sql (Flyway migration)
- create_chat(), get_chats_by_user_id(), get_chat_by_id() in database.py
</context>

<implementation>
Follow TDD approach:
1. Tests will be created from Gherkin scenarios
2. Implement code to make tests pass
3. Ensure all scenarios are green

Architecture Guidelines:
- Follow existing patterns in database.py
- Use uuid.uuid4() for chat id generation
- Foreign key ON DELETE CASCADE for user cleanup
- 500 lines max per file, interfaces, no env vars in functions
</implementation>

<verification>
All Gherkin scenarios must pass:
- [ ] Scenario: User creates a chat and retrieves it
- [ ] Scenario: User cannot see another user's chats
- [ ] Scenario: User retrieves their filtered chat list
</verification>

<success_criteria>
- All Gherkin scenarios pass
- V2 migration creates chats table with proper schema
- Repository functions follow existing patterns
- User isolation enforced at data layer
- Code follows project coding standards
</success_criteria>
