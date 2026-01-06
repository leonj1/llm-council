# DRAFT: User Chat Persistence in MySQL

## Overview
Implement database persistence for user chats and messages, replacing JSON file storage with MySQL. Chats are associated with authenticated users via foreign key, and authorization checks ensure users can only access their own data.

## Traces to Root Request
| Component | Root Request Term | Justification |
|-----------|-------------------|---------------|
| V2 chats table migration | "database tables for chats" | Creates chats table with user_id FK |
| V3 messages table migration | "database tables for messages" | Creates messages table with stage1/2/3 JSON |
| Updated storage.py | "MySQL instead of JSON files" | Replaces file I/O with database queries |
| user_id in chats | "user_id foreign key" | Associates chats with authenticated users |
| API endpoint updates | "filter chats by authenticated user" | WHERE user_id = ? in queries |
| stage1/2/3 columns | "LLM responses persisted" | JSON columns store all council stages |
| Authorization checks | "users can only access their own chats" | Verify ownership before returning data |

---

## Interfaces Needed

### IChatRepository
```python
interface IChatRepository:
    def create_chat(user_id: int, title: str, chat_type: str) -> Chat
    def get_chat(chat_id: str, user_id: int) -> Optional[Chat]
    def list_chats(user_id: int) -> List[ChatSummary]
    def delete_chat(chat_id: str, user_id: int) -> bool
    def update_chat_title(chat_id: str, user_id: int, title: str) -> bool
```

### IMessageRepository
```python
interface IMessageRepository:
    def add_user_message(chat_id: str, user_id: int, content: str) -> Message
    def add_assistant_message(chat_id: str, user_id: int, stage1: dict, stage2: dict, stage3: dict) -> Message
    def get_messages(chat_id: str, user_id: int) -> List[Message]
```

### IAuthorizationService
```python
interface IAuthorizationService:
    def authorize_chat_access(chat_id: str, user_id: int) -> bool
    def get_chat_owner(chat_id: str) -> Optional[int]
```

---

## Data Models

### Chat (Database Table: chats)
```sql
-- V2__create_chats_table.sql
CREATE TABLE chats (
    id VARCHAR(36) PRIMARY KEY,           -- UUID
    user_id INT NOT NULL,                  -- FK to users.id
    title VARCHAR(255) DEFAULT 'New Conversation',
    type VARCHAR(50) DEFAULT 'council',    -- 'council' or 'movie_script'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### Message (Database Table: messages)
```sql
-- V3__create_messages_table.sql
CREATE TABLE messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    chat_id VARCHAR(36) NOT NULL,          -- FK to chats.id
    role ENUM('user', 'assistant') NOT NULL,
    content TEXT,                           -- User message content
    stage1 JSON,                            -- Stage 1 responses (assistant only)
    stage2 JSON,                            -- Stage 2 rankings (assistant only)
    stage3 JSON,                            -- Stage 3 synthesis (assistant only)
    stage4 JSON,                            -- Stage 4 for movie_script type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE,
    INDEX idx_chat_id (chat_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### Python Data Classes
```python
@dataclass
class Chat:
    id: str
    user_id: int
    title: str
    type: str
    created_at: datetime
    updated_at: datetime

@dataclass
class ChatSummary:
    id: str
    title: str
    type: str
    created_at: datetime
    message_count: int

@dataclass
class Message:
    id: int
    chat_id: str
    role: str
    content: Optional[str]
    stage1: Optional[dict]
    stage2: Optional[dict]
    stage3: Optional[dict]
    stage4: Optional[dict]
    created_at: datetime
```

---

## Logic Flow

### Create Chat
```
1. Receive request with user_id from session
2. Generate UUID for chat_id
3. INSERT INTO chats (id, user_id, title, type)
4. Return Chat object
```

### List Chats (with message count)
```
1. Receive request with user_id from session
2. SELECT c.*, COUNT(m.id) as message_count
   FROM chats c
   LEFT JOIN messages m ON c.id = m.chat_id
   WHERE c.user_id = ?
   GROUP BY c.id
   ORDER BY c.created_at DESC
3. Return List[ChatSummary]
```

### Get Chat Messages (with authorization)
```
1. Receive chat_id and user_id from session
2. SELECT user_id FROM chats WHERE id = ?
3. IF chat.user_id != request.user_id:
      RETURN 403 Forbidden
4. SELECT * FROM messages WHERE chat_id = ? ORDER BY created_at
5. Return List[Message]
```

### Add User Message
```
1. Verify chat ownership (step 2-3 above)
2. INSERT INTO messages (chat_id, role, content)
   VALUES (?, 'user', ?)
3. Return Message
```

### Add Assistant Message
```
1. Verify chat ownership
2. INSERT INTO messages (chat_id, role, stage1, stage2, stage3)
   VALUES (?, 'assistant', JSON(?), JSON(?), JSON(?))
3. Return Message
```

### Authorization Check
```
1. Query: SELECT user_id FROM chats WHERE id = ?
2. IF no result: RETURN 404 Not Found
3. IF chat.user_id != request.user_id: RETURN 403 Forbidden
4. ELSE: Proceed with operation
```

---

## API Endpoint Changes

### Existing Endpoints to Modify
| Endpoint | Change Required |
|----------|-----------------|
| POST /api/conversations | Add user_id from session, insert to MySQL |
| GET /api/conversations | Filter by user_id, query MySQL |
| GET /api/conversations/{id} | Verify ownership, query MySQL |
| POST /api/conversations/{id}/message | Verify ownership, insert to MySQL |
| DELETE /api/conversations/{id} | Verify ownership, delete from MySQL |

### Error Responses
- 401 Unauthorized: No session/authentication
- 403 Forbidden: User doesn't own the chat
- 404 Not Found: Chat doesn't exist

---

## Context Budget

| Category | Count | Lines |
|----------|-------|-------|
| Files to read | 4 | ~300 lines |
| - storage.py | | 80 lines |
| - database.py | | 50 lines |
| - V1 migration | | 15 lines |
| - main.py (endpoints) | | 150 lines |
| New code to write | | ~200 lines |
| - V2 migration | | 20 lines |
| - V3 migration | | 25 lines |
| - storage.py update | | 150 lines |
| Test code to write | | ~100 lines |
| **Estimated context usage** | | **35%** |

---

## Dependencies
- MySQL database with Flyway migrations
- Existing users table (V1)
- Session-based authentication from auth.py
- mysql-connector-python library

## Risks
- Data migration: Existing JSON conversations will not be migrated
- JSON column size: Large stage1/2/3 data may hit MySQL JSON limits (1GB, unlikely)
- Transaction handling: Need proper rollback on multi-insert failures

## Success Criteria (from BDD)
1. User creates chat -> retrievable from database with user_id
2. User A's chats not visible to User B
3. User messages persisted with content and timestamp
4. Stage 1/2/3 data stored and retrievable
5. Multiple exchanges ordered correctly
6. Chat list shows metadata (title, count, timestamp)
7. Session persistence: data survives re-auth
8. Unauthenticated requests return 401
9. Cross-user access attempts return 403
