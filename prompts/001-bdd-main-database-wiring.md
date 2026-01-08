---
executor: bdd
source_feature: ./tests/bdd/main-database-wiring.feature
---

<objective>
Implement the Main API Database Wiring feature as defined by the BDD scenarios below.
Wire main.py to use database.py for MySQL persistence instead of storage.py for JSON file storage.
The implementation must make all Gherkin scenarios pass.
</objective>

<gherkin>
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
</gherkin>

<requirements>
Based on the Gherkin scenarios, implement:

1. Replace storage.create_conversation() with database.create_chat()
   - POST /api/conversations must use database.create_chat(user_id)
   - Response must translate chat_id to conversation format with "id" field

2. Replace storage.add_user_message() with database.create_message()
   - User messages: role="user", content=message text
   - Stage data columns (stage1_data, stage2_data, stage3_data) must be None

3. Replace storage.add_assistant_message() with database.create_message()
   - Assistant messages: role="assistant"
   - Unpack stage data into separate columns:
     - stage1_data: stage 1 model responses
     - stage2_data: stage 2 rankings
     - stage3_data: stage 3 synthesis
   - Content field: final synthesized answer from stage3["response"]

4. Replace storage.get_conversation() with database.get_chat_by_id() + get_messages_by_chat_id()
   - GET /api/conversations/{id} must retrieve chat and messages separately
   - Response must use "id" field (API convention, not "chat_id")
   - All messages must be included in response

Edge Cases to Handle:
- Conversation not found returns 404
- User ID from auth must be passed to database functions
- Messages must preserve chronological order
</requirements>

<context>
BDD Specification: specs/BDD-SPEC-storage-layer-migration.md
Gap Analysis: specs/GAP-ANALYSIS.md

Reuse Opportunities (from gap analysis):
- database.py is FULLY IMPLEMENTED with all needed functions:
  - create_chat(user_id) - returns chat with id
  - get_chat_by_id(chat_id) - returns chat record
  - create_message(chat_id, role, content, stage1_data, stage2_data, stage3_data)
  - get_messages_by_chat_id(chat_id) - returns messages in order
- JSON serialization/deserialization handled by database.py
- Auth dependency (require_auth) already exists in main.py

New Components Needed:
- None - only wiring changes in main.py

Schema Translation:
| API Convention | Database Convention |
|----------------|---------------------|
| conversation_id | chat_id |
| message.stage1 | stage1_data |
| message.stage2 | stage2_data |
| message.stage3 | stage3_data |
</context>

<implementation>
Follow TDD approach:
1. Tests will be created from Gherkin scenarios
2. Implement code to make tests pass
3. Ensure all scenarios are green

Architecture Guidelines:
- Import database module: `from . import database`
- Keep storage import for movie_script endpoints (out of scope)
- Build API response format inline (id, created_at, messages)
- Use existing require_auth dependency for user_id

Code Changes in main.py:

1. Add import:
   ```python
   from . import database
   ```

2. create_conversation endpoint:
   ```python
   chat = database.create_chat(user["user_id"])
   return {"id": chat["id"], "created_at": str(chat["created_at"]), ...}
   ```

3. get_conversation endpoint:
   ```python
   chat = database.get_chat_by_id(conversation_id)
   messages = database.get_messages_by_chat_id(conversation_id)
   # Format messages: stage1_data -> stage1, etc.
   ```

4. send_message endpoint - user message:
   ```python
   database.create_message(conversation_id, "user", request.content, None, None, None)
   ```

5. send_message endpoint - assistant message:
   ```python
   content = stage3_result.get("response", "")
   database.create_message(conversation_id, "assistant", content, stage1_results, stage2_results, stage3_result)
   ```
</implementation>

<verification>
All Gherkin scenarios must pass:
- [ ] Scenario: Create conversation stores to database
- [ ] Scenario: Add user message stores with user role
- [ ] Scenario: Add assistant message stores stage data separately
- [ ] Scenario: Get conversation retrieves from database
</verification>

<success_criteria>
- All Gherkin scenarios pass
- Code follows project coding standards
- Tests provide complete coverage of scenarios
- Implementation matches user's confirmed intent
- API response format unchanged (backward compatible)
- Database functions called instead of storage functions
</success_criteria>
