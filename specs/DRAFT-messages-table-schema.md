# DRAFT: Messages Table Schema

## Root Request Trace
> "Creating database tables for...messages", "Stage 1, 2, 3...persisted and retrievable from the database"

## Overview
Create MySQL table and CRUD functions for storing chat messages with LLM stage data.

## Interfaces Needed

### IMessageRepository
```python
interface IMessageRepository:
    def create_message(chat_id: str, role: str, content: str,
                       stage1: Optional[dict], stage2: Optional[dict],
                       stage3: Optional[dict]) -> Optional[dict]
    def get_messages_by_chat_id(chat_id: str) -> List[dict]
    def get_message_by_id(message_id: int) -> Optional[dict]
```

## Data Models

### Messages Table (V3 Migration)
```sql
CREATE TABLE messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    chat_id VARCHAR(36) NOT NULL,
    role ENUM('user', 'assistant') NOT NULL,
    content TEXT NOT NULL,
    stage1_data JSON DEFAULT NULL,
    stage2_data JSON DEFAULT NULL,
    stage3_data JSON DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_chat_id (chat_id),
    FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### Message Dict (Python)
```python
{
    "id": int,
    "chat_id": str,
    "role": "user" | "assistant",
    "content": str,
    "stage1_data": Optional[dict],
    "stage2_data": Optional[dict],
    "stage3_data": Optional[dict],
    "created_at": datetime
}
```

## Logic Flow

### create_message
```
1. Validate chat_id exists in chats table
2. Serialize stage1/2/3 dicts to JSON strings (if provided)
3. INSERT INTO messages (chat_id, role, content, stage1_data, stage2_data, stage3_data)
4. Return created message record
```

### get_messages_by_chat_id
```
1. SELECT * FROM messages WHERE chat_id = ? ORDER BY created_at ASC
2. Deserialize JSON columns to dicts
3. Return list of message dicts
```

### get_message_by_id
```
1. SELECT * FROM messages WHERE id = ?
2. Deserialize JSON columns to dicts
3. Return message dict or None
```

## Files to Create/Modify

| File | Action | Lines |
|------|--------|-------|
| sql/V3__create_messages_table.sql | Create | ~15 |
| backend/database.py | Modify (add 3 functions) | ~60 |
| backend/tests/test_messages_table_schema.py | Create | ~80 |

## BDD Scenarios (5)

1. **Store user message in database**
   - Given a chat exists
   - When I create a user message with content
   - Then the message is persisted with role=user

2. **Store assistant message with stage data**
   - Given a chat exists
   - When I create an assistant message with stage1/2/3 JSON
   - Then all stage data is persisted

3. **Retrieve messages by chat ID**
   - Given a chat with 3 messages
   - When I get_messages_by_chat_id
   - Then I receive messages in chronological order

4. **Retrieve single message by ID**
   - Given a message exists
   - When I get_message_by_id
   - Then I receive the message with deserialized stage data

5. **Messages cascade delete with chat**
   - Given a chat with messages
   - When the chat is deleted
   - Then all associated messages are deleted

## Context Budget

| Metric | Estimate |
|--------|----------|
| Files to read | 2 (~200 lines) |
| New code to write | ~75 lines |
| Test code to write | ~80 lines |
| Total context | ~355 lines |
| Estimated context usage | ~15% |

## Dependencies
- V2 migration (chats table) must be applied first
- Existing database.py cursor context manager
