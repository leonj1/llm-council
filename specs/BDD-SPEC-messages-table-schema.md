# BDD Specification: Messages Table Schema

## Overview
Create MySQL messages table with chat_id foreign key and CRUD operations for storing user queries and LLM responses (Stage 1/2/3 data).

## Root Request Trace
> "Creating database tables for...messages", "Stage 1, 2, 3...persisted and retrievable from the database"

## User Stories
- As an authenticated user, I want my messages to be stored with chat association and stage data so that my queries and LLM responses are persisted and retrievable

## Feature Files

| Feature File | Scenarios | Coverage |
|--------------|-----------|----------|
| messages-table-schema.feature | 5 | User message storage, assistant stage data, single message retrieval, chronological order, cascade delete |

## Scenarios Summary

### messages-table-schema.feature

1. **User message is stored and retrieved with content**
   - Validates user messages are persisted with content, timestamp, and chat association

2. **Assistant message is stored with Stage 1, 2, 3 data and retrieved**
   - Validates assistant messages store and retrieve all three stage JSON data fields

3. **Single message is retrieved by ID with stage data**
   - Validates get_message_by_id returns a single message with all stage data fields

4. **Messages are retrieved in chronological order**
   - Validates messages are returned ordered by creation time (ascending)

5. **Messages are deleted when parent chat is deleted**
   - Validates cascade delete removes all messages when parent chat is deleted

## Acceptance Criteria

### User Message Storage
- User message content is persisted exactly as provided
- User message has role = "user"
- User message has creation timestamp
- User message is associated with correct chat_id

### Assistant Message with Stage Data
- Assistant message stores stage1_data JSON
- Assistant message stores stage2_data JSON
- Assistant message stores stage3_data JSON
- All stage data is retrievable and deserializable

### Single Message Retrieval
- get_message_by_id returns message by primary key
- Returned message includes all stage data (stage1, stage2, stage3)
- Returns None/null if message ID does not exist

### Chronological Ordering
- Messages returned in ascending order by created_at
- Order is consistent across multiple queries

### Cascade Delete
- Deleting a chat removes all associated messages
- Foreign key constraint enforces referential integrity
- No orphan messages remain after chat deletion

## Technical Notes

### Database Schema (V3 Migration)
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
);
```

### Repository Interface
```python
interface IMessageRepository:
    def create_message(chat_id, role, content, stage1, stage2, stage3) -> dict
    def get_messages_by_chat_id(chat_id) -> List[dict]
    def get_message_by_id(message_id) -> Optional[dict]
```

## Dependencies
- V2 migration (chats table) must exist for foreign key
- Existing database.py cursor context manager
