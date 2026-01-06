# DRAFT: Storage Layer Migration

## Summary
Create a new `chat_storage.py` module that provides MySQL-backed storage operations for user chats and messages, replacing the JSON file operations in `storage.py` with calls to the existing `database.py` functions.

## Root Request Traceability
| Requirement Term | How This Spec Addresses It |
|------------------|----------------------------|
| "Updating storage.py to use MySQL instead of JSON files" | New chat_storage.py wraps database.py functions |
| "retrievable from database" | All get/list operations query MySQL |
| "Stage 1, 2, 3...persisted" | Stage data passed through to create_message |
| "user_id...to associate chats with authenticated users" | user_id required param on all chat operations |

## Interfaces Needed

### IChatStorage (Protocol)
```python
from typing import Protocol, List, Dict, Any, Optional

class IChatStorage(Protocol):
    """Interface for chat storage operations."""

    def create_chat(self, user_id: int, chat_type: str = "council") -> Optional[Dict[str, Any]]:
        """Create new chat for user. Returns chat dict or None."""
        ...

    def get_chat(self, chat_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        """Get chat by ID. Returns None if not found or wrong user."""
        ...

    def list_chats(self, user_id: int) -> List[Dict[str, Any]]:
        """List all chats for user with metadata."""
        ...

    def delete_chat(self, chat_id: str, user_id: int) -> bool:
        """Delete chat. Returns False if not found or wrong user."""
        ...

    def add_user_message(self, chat_id: str, user_id: int, content: str) -> Optional[Dict[str, Any]]:
        """Add user message to chat. Returns message or None."""
        ...

    def add_assistant_message(
        self,
        chat_id: str,
        user_id: int,
        stage1: List[Dict[str, Any]],
        stage2: List[Dict[str, Any]],
        stage3: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Add assistant message with stage data. Returns message or None."""
        ...

    def get_messages(self, chat_id: str, user_id: int) -> List[Dict[str, Any]]:
        """Get all messages for chat. Empty list if wrong user."""
        ...
```

## Data Models

### Chat (returned from create_chat, get_chat)
```python
{
    "id": str,          # UUID
    "user_id": int,
    "created_at": datetime,
    "title": str,       # Default "New Conversation"
    "type": str,        # "council" or "movie_script"
    "message_count": int  # Only in list_chats
}
```

### Message (returned from add_*_message, get_messages)
```python
{
    "id": int,
    "chat_id": str,
    "role": str,        # "user" or "assistant"
    "content": str,
    "stage1_data": Optional[List[Dict]],
    "stage2_data": Optional[List[Dict]],
    "stage3_data": Optional[Dict],
    "created_at": datetime
}
```

## Logic Flow

### create_chat(user_id, chat_type)
```
1. Call database.create_chat(user_id)
2. If None, return None
3. Return enriched dict with title="New Conversation", type=chat_type
```

### get_chat(chat_id, user_id)
```
1. Call database.get_chat_by_id(chat_id)
2. If None, return None
3. If chat.user_id != user_id, return None  # Authorization
4. Enrich with message_count via get_messages_by_chat_id
5. Return chat dict
```

### list_chats(user_id)
```
1. Call database.get_chats_by_user_id(user_id)
2. For each chat, count messages
3. Return list with metadata (title, type, message_count)
```

### delete_chat(chat_id, user_id)
```
1. Call database.get_chat_by_id(chat_id)
2. If None or chat.user_id != user_id, return False
3. Call database.delete_chat(chat_id)
4. Return result
```

### add_user_message(chat_id, user_id, content)
```
1. Verify chat ownership via get_chat(chat_id, user_id)
2. If None, return None
3. Call database.create_message(chat_id, "user", content, None, None, None)
4. Return message dict
```

### add_assistant_message(chat_id, user_id, stage1, stage2, stage3)
```
1. Verify chat ownership via get_chat(chat_id, user_id)
2. If None, return None
3. Extract content from stage3["content"] for display
4. Call database.create_message(chat_id, "assistant", content, stage1, stage2, stage3)
5. Return message dict
```

### get_messages(chat_id, user_id)
```
1. Verify chat ownership via get_chat(chat_id, user_id)
2. If None, return []
3. Call database.get_messages_by_chat_id(chat_id)
4. Return messages list
```

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| backend/chat_storage.py | CREATE | MySQL-backed storage module |
| backend/tests/test_chat_storage.py | CREATE | Unit tests for chat_storage |

## BDD Scenarios (4)

### Scenario 1: Chat creation persists to MySQL
```gherkin
Given a user with id 1 exists
When I create a chat for user 1
Then the chat should be stored in MySQL
And the chat should have user_id 1
```

### Scenario 2: User message persistence
```gherkin
Given a chat exists for user 1
When I add a user message "Hello"
Then the message should be stored in MySQL
And the message role should be "user"
```

### Scenario 3: Assistant message with stages
```gherkin
Given a chat exists for user 1
When I add an assistant message with stage1, stage2, stage3 data
Then all three stages should be stored as JSON
And the message role should be "assistant"
```

### Scenario 4: User isolation on retrieval
```gherkin
Given user 1 has a chat
And user 2 exists
When user 2 tries to get user 1's chat
Then the result should be None
```

## Context Budget

| Category | Estimate |
|----------|----------|
| Files to read | 2 (~400 lines) - database.py, storage.py |
| New code to write | ~150 lines |
| Test code to write | ~100 lines |
| Total files | 2 new files |
| Estimated context usage | 25% |

## Dependencies

- database.py (existing) - provides raw MySQL operations
- storage.py (existing) - kept for backward compatibility, not modified

## Notes

- Keep existing storage.py unchanged for backward compatibility
- chat_storage.py is a thin wrapper adding user authorization
- Stage data stored as JSON in MySQL TEXT columns
- Authorization is enforced at storage layer, not just API
