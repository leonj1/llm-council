---
executor: bdd
source_feature: ./tests/bdd/messages-table-schema.feature
---

<objective>
Implement the Messages Table Schema feature as defined by the BDD scenarios below.
Create Flyway migration V3 for the messages table with chat_id foreign key and JSON stage data columns.
Add message repository functions to database.py.
The implementation must make all Gherkin scenarios pass.
</objective>

<gherkin>
Feature: Messages Table Schema
  As an authenticated user
  I want my messages to be stored with chat association and stage data
  So that my queries and LLM responses are persisted and retrievable

  Background:
    Given the database is available
    And a user "alice@example.com" exists
    And alice has created a chat

  # User Message Storage

  Scenario: User message is stored and retrieved with content
    When alice creates a user message with content "What is machine learning?"
    And alice fetches messages for the chat
    Then the messages contain a user message
    And the user message content equals "What is machine learning?"
    And the user message has a creation timestamp
    And the user message belongs to alice's chat

  # Assistant Message with Stage Data

  Scenario: Assistant message is stored with Stage 1, 2, 3 data and retrieved
    When alice creates an assistant message with stage data
    And the stage 1 data contains model responses
    And the stage 2 data contains rankings
    And the stage 3 data contains the synthesis
    And alice fetches messages for the chat
    Then the messages contain an assistant message
    And the assistant message has stage 1 data with model responses
    And the assistant message has stage 2 data with rankings
    And the assistant message has stage 3 data with synthesis

  # Chronological Order

  Scenario: Messages are retrieved in chronological order
    Given alice has created 3 messages in the chat over time
    When alice fetches messages for the chat
    Then the messages are returned in chronological order
    And the first message was created before the second message
    And the second message was created before the third message

  # Single Message Retrieval

  Scenario: Single message is retrieved by ID with stage data
    Given alice has created an assistant message with stage data
    When alice fetches the message by its ID
    Then the message is returned
    And the message has stage 1 data with model responses
    And the message has stage 2 data with rankings
    And the message has stage 3 data with synthesis

  # Cascade Delete

  Scenario: Messages are deleted when parent chat is deleted
    Given alice has created 2 messages in the chat
    When alice deletes the chat
    Then the chat no longer exists
    And the messages associated with the chat are also deleted
</gherkin>

<requirements>
Based on the Gherkin scenarios, implement:

1. Flyway migration V3 for messages table (`sql/V3__create_messages_table.sql`)
   - id: INT AUTO_INCREMENT PRIMARY KEY
   - chat_id: VARCHAR(36) NOT NULL with foreign key to chats(id)
   - role: ENUM('user', 'assistant') NOT NULL
   - content: TEXT NOT NULL
   - stage1_data: JSON DEFAULT NULL
   - stage2_data: JSON DEFAULT NULL
   - stage3_data: JSON DEFAULT NULL
   - created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   - Index on chat_id for efficient queries
   - ON DELETE CASCADE for referential integrity

2. Repository function: `create_message(chat_id, role, content, stage1_data, stage2_data, stage3_data) -> Optional[dict]`
   - Insert message with all fields
   - Handle JSON serialization for stage data
   - Return created message record

3. Repository function: `get_messages_by_chat_id(chat_id: str) -> List[dict]`
   - Return all messages for the given chat
   - Order by created_at ascending (chronological)
   - Include all stage data in returned records

4. Repository function: `get_message_by_id(message_id: int) -> Optional[dict]`
   - Return single message by id
   - Include all stage data fields

5. Repository function: `delete_chat(chat_id: str) -> bool`
   - Delete chat by id
   - Messages cascade-deleted via foreign key
   - Return True if deleted, False otherwise

Edge Cases to Handle:
- Database unavailable (return None/empty list)
- Non-existent chat_id (foreign key constraint)
- Empty messages list for chat with no messages
- Null stage data for user messages
- JSON serialization/deserialization
</requirements>

<context>
BDD Specification: specs/BDD-SPEC-messages-table-schema.md
Gap Analysis: specs/GAP-ANALYSIS.md

Reuse Opportunities (from gap analysis):
- `get_db_cursor()` context manager from database.py
- `get_user_by_email()` for test setup
- `create_chat()` for test setup
- `get_chat_by_id()` for validation
- Pattern: Functions return Optional[dict] with dictionary cursor
- Pattern: InnoDB engine, utf8mb4 charset for migrations
- Pattern: ON DELETE CASCADE for foreign keys

New Components Needed:
- sql/V3__create_messages_table.sql (Flyway migration)
- create_message(), get_messages_by_chat_id(), get_message_by_id(), delete_chat() in database.py
</context>

<implementation>
Follow TDD approach:
1. Tests will be created from Gherkin scenarios
2. Implement code to make tests pass
3. Ensure all scenarios are green

Architecture Guidelines:
- Follow existing patterns in database.py
- Use json.dumps() for stage data serialization when inserting
- Foreign key ON DELETE CASCADE ensures cascade delete
- 500 lines max per file, interfaces, no env vars in functions

JSON Handling:
```python
import json

# When inserting stage data:
cursor.execute(
    "INSERT INTO messages (chat_id, role, content, stage1_data, stage2_data, stage3_data) VALUES (%s, %s, %s, %s, %s, %s)",
    (chat_id, role, content,
     json.dumps(stage1_data) if stage1_data else None,
     json.dumps(stage2_data) if stage2_data else None,
     json.dumps(stage3_data) if stage3_data else None)
)
```
</implementation>

<verification>
All Gherkin scenarios must pass:
- [ ] Scenario: User message is stored and retrieved with content
- [ ] Scenario: Assistant message is stored with Stage 1, 2, 3 data and retrieved
- [ ] Scenario: Messages are retrieved in chronological order
- [ ] Scenario: Single message is retrieved by ID with stage data
- [ ] Scenario: Messages are deleted when parent chat is deleted
</verification>

<success_criteria>
- All 5 Gherkin scenarios pass
- V3 migration creates messages table with proper schema
- Repository functions follow existing patterns in database.py
- JSON stage data is properly serialized/deserialized
- Cascade delete works correctly
- Code follows project coding standards
</success_criteria>
