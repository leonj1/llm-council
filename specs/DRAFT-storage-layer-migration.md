# DRAFT: Wire main.py to database.py for MySQL Persistence

## Summary
Replace storage.py function calls in main.py with direct calls to database.py. Handle schema translation between storage conventions (conversation_id, full message object) and database conventions (chat_id, separate columns).

## Root Request Traceability
| Root Request Term | How This Spec Addresses It |
|-------------------|----------------------------|
| "Wire main.py to use database.py" | Direct imports and calls to database.py in main.py |
| "instead of storage.py" | Remove storage.py imports, replace all storage.* calls |
| "storage.create_conversation() → database.create_chat()" | Explicit replacement in conversation creation endpoint |
| "storage.add_user_message() → database.create_message()" | Replace with database.create_message(role="user") |
| "storage.add_assistant_message() → database.create_message()" | Replace with database.create_message(role="assistant") |
| "conversation_id vs chat_id" | Translate API param conversation_id to database chat_id |
| "separate columns for content, stage1_data, stage2_data, stage3_data" | Unpack message object into separate params |

## Interfaces Needed

None. This is direct wiring - no new abstractions.

## Data Models

### Schema Translation Map
```python
# API/Storage convention → Database convention
"conversation_id"     → "chat_id"
"conversation"        → "chat"
message["content"]    → content param
message["stage1"]     → stage1_data param
message["stage2"]     → stage2_data param
message["stage3"]     → stage3_data param
```

## Logic Flow

### Endpoint: POST /api/conversations (Create)
```
BEFORE: storage.create_conversation()
AFTER:  database.create_chat(user_id)
        # Returns chat with chat_id
        # Response: translate chat_id → conversation_id for API compat
```

### Endpoint: GET /api/conversations/{conversation_id}
```
BEFORE: storage.get_conversation(conversation_id)
AFTER:  database.get_chat_by_id(conversation_id)
        database.get_messages_by_chat_id(conversation_id)
        # Assemble response matching API format
```

### Endpoint: POST /api/conversations/{conversation_id}/message
```
BEFORE:
  storage.add_user_message(conversation_id, content)
  storage.add_assistant_message(conversation_id, {stage1, stage2, stage3})

AFTER:
  database.create_message(
    chat_id=conversation_id,
    role="user",
    content=content,
    stage1_data=None,
    stage2_data=None,
    stage3_data=None
  )
  database.create_message(
    chat_id=conversation_id,
    role="assistant",
    content=stage3["content"],
    stage1_data=stage1,
    stage2_data=stage2,
    stage3_data=stage3
  )
```

### Endpoint: GET /api/conversations
```
BEFORE: storage.list_conversations()
AFTER:  database.get_chats_by_user_id(user_id)
        # Translate each chat_id → conversation_id in response
```

## Files to Modify

| File | Action | Changes |
|------|--------|---------|
| backend/main.py | MODIFY | Replace storage.* imports with database.*, update all endpoint implementations |

## BDD Scenarios (4)

### Scenario 1: Create conversation uses database.create_chat
```gherkin
Given main.py is wired to database.py
When POST /api/conversations is called
Then database.create_chat() should be invoked
And the response should contain conversation_id (translated from chat_id)
```

### Scenario 2: Add user message uses database.create_message
```gherkin
Given a conversation exists with id "abc123"
When POST /api/conversations/abc123/message is called with content "Hello"
Then database.create_message() should be invoked with:
  | param | value |
  | chat_id | abc123 |
  | role | user |
  | content | Hello |
  | stage1_data | None |
  | stage2_data | None |
  | stage3_data | None |
```

### Scenario 3: Add assistant message unpacks stages to separate columns
```gherkin
Given a conversation exists with id "abc123"
And stage1_data is [{"model": "gpt-4", "response": "..."}]
And stage2_data is [{"model": "gpt-4", "ranking": "..."}]
And stage3_data is {"content": "Final answer", "model": "gemini"}
When the assistant message is added
Then database.create_message() should be invoked with:
  | param | value |
  | chat_id | abc123 |
  | role | assistant |
  | content | Final answer |
  | stage1_data | [{"model": "gpt-4", "response": "..."}] |
  | stage2_data | [{"model": "gpt-4", "ranking": "..."}] |
  | stage3_data | {"content": "Final answer", "model": "gemini"} |
```

### Scenario 4: Get conversation translates chat_id to conversation_id
```gherkin
Given database.get_chat_by_id("abc123") returns a chat
When GET /api/conversations/abc123 is called
Then the response should use "id" or "conversation_id" (not "chat_id")
And messages should be retrieved via database.get_messages_by_chat_id()
```

## Context Budget

| Category | Estimate |
|----------|----------|
| Files to read | 2 (~300 lines) - main.py, database.py |
| Code to modify | ~80 lines in main.py |
| Test code to write | ~60 lines |
| Estimated context usage | 15% |

## What This Spec Does NOT Include (Per User Request)

- No new wrapper module (chat_storage.py) - direct wiring
- No user isolation logic - not requested
- No chat deletion - not requested
- No chat types/titles - not requested
- No error handling beyond existing - not requested

## Dependencies

- database.py (existing) - provides create_chat, create_message, get_chat_by_id, get_messages_by_chat_id, get_chats_by_user_id
