# Gap Analysis: Storage Layer Migration

## Analysis Date: 2026-01-07

## Executive Summary

Wire main.py to use database.py for MySQL persistence instead of storage.py for JSON file storage. The database module is FULLY IMPLEMENTED. Only wiring changes needed in main.py.

## Root Request Trace
> "Wire main.py to use database.py", "Store conversations in MySQL", "Replace JSON file storage"

## Existing Code to Reuse

### 1. Database Layer (backend/database.py) - COMPLETE

| Function | Purpose | Ready |
|----------|---------|-------|
| `create_chat(user_id)` | Create conversation | YES |
| `get_chat_by_id(chat_id)` | Get conversation | YES |
| `get_chats_by_user_id(user_id)` | List conversations | YES |
| `create_message(chat_id, role, content, s1, s2, s3)` | Store message | YES |
| `get_messages_by_chat_id(chat_id)` | Get messages | YES |
| `delete_chat(chat_id)` | Delete conversation | YES |

### 2. Storage Layer (backend/storage.py) - TO BE REPLACED

| Current Function | Database Replacement |
|------------------|---------------------|
| `storage.create_conversation(id, user_id, type)` | `database.create_chat(user_id)` |
| `storage.get_conversation(id)` | `database.get_chat_by_id(id)` + `get_messages_by_chat_id(id)` |
| `storage.list_conversations(user_id)` | `database.get_chats_by_user_id(user_id)` |
| `storage.add_user_message(id, content)` | `database.create_message(id, 'user', content, None, None, None)` |
| `storage.add_assistant_message(id, s1, s2, s3)` | `database.create_message(id, 'assistant', content, s1, s2, s3)` |
| `storage.delete_conversation(id)` | `database.delete_chat(id)` |

## Schema Translation

### API Convention vs Database Convention

| API | Database |
|-----|----------|
| `conversation_id` | `chat_id` |
| `conversation` | `chat` |
| `message.stage1` | `stage1_data` |
| `message.stage2` | `stage2_data` |
| `message.stage3` | `stage3_data` |

### Response Format Translation

**API expects**:
```json
{
  "id": "uuid",
  "created_at": "timestamp",
  "title": "string",
  "type": "council",
  "messages": [...]
}
```

**Database returns**:
```json
{
  "id": "uuid",
  "user_id": 123,
  "created_at": "datetime"
}
```

**Translation**: Build response inline in main.py endpoints.

## Code Needing Modification

### main.py - Endpoint Changes

| Line | Endpoint | Current | Target |
|------|----------|---------|--------|
| 140 | GET /conversations | `storage.list_conversations` | `database.get_chats_by_user_id` |
| 150 | POST /conversations | `storage.create_conversation` | `database.create_chat` |
| 157 | GET /conversations/{id} | `storage.get_conversation` | `database.get_chat_by_id` + messages |
| 179 | DELETE /conversations/{id} | `storage.delete_conversation` | `database.delete_chat` |
| 227 | POST /{id}/message | `storage.add_user_message` | `database.create_message` |
| 241 | POST /{id}/message | `storage.add_assistant_message` | `database.create_message` |

## New Components to Build

**None** - All database functions exist. Only wiring changes.

## Out of Scope (Per BDD Spec)

- Title storage (DB has no title column)
- Conversation type (DB has no type column)
- User isolation logic
- Error handling beyond existing

## Refactoring Decision

**Refactoring Needed**: No
**Reason**: Direct function call replacement only

## GO Signal

**STATUS: GO**

Rationale:
1. database.py is complete and tested
2. No structural refactoring required
3. Direct wiring changes in main.py
4. Schema translation is straightforward

## Implementation Order

1. Replace storage import with database import
2. Update create_conversation endpoint
3. Update get_conversation endpoint
4. Update send_message endpoint (user + assistant messages)
5. Update delete_conversation endpoint
6. Update list_conversations endpoint

## Files to Modify

| File | Action |
|------|--------|
| `backend/main.py` | Replace storage calls with database calls |

## Files to Keep Unchanged

| File | Reason |
|------|--------|
| `backend/database.py` | Already complete |
| `backend/storage.py` | Keep as fallback |
