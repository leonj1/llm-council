# DRAFT: Database Schema - Chats Table

## Overview
Create the foundational `chats` table with user association via foreign key to enable user-scoped chat persistence.

## Root Request Trace
- "Creating database tables for chats...linked to users"
- "user_id foreign key to associate chats with authenticated users"

## Interfaces Needed

### IChatRepository
```python
from abc import ABC, abstractmethod
from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Chat:
    id: str
    user_id: int
    created_at: datetime
    title: Optional[str] = None

class IChatRepository(ABC):
    @abstractmethod
    async def create(self, user_id: int, chat_id: Optional[str] = None) -> Chat:
        """Create a new chat for a user. Returns Chat object."""
        pass

    @abstractmethod
    async def get_by_id(self, chat_id: str) -> Optional[Chat]:
        """Retrieve chat by ID. Returns None if not found."""
        pass

    @abstractmethod
    async def get_by_user(self, user_id: int) -> List[Chat]:
        """Get all chats belonging to a user."""
        pass

    @abstractmethod
    async def delete(self, chat_id: str) -> bool:
        """Delete chat by ID. Returns True if deleted."""
        pass
```

## Data Models

### SQL Migration (V2__create_chats_table.sql)
```sql
CREATE TABLE chats (
    id VARCHAR(36) PRIMARY KEY,
    user_id BIGINT NOT NULL,
    title VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_chats_user_id (user_id),
    INDEX idx_chats_created_at (created_at)
);
```

### Python Dataclass
```python
@dataclass
class Chat:
    id: str              # UUID string
    user_id: int         # FK to users.id
    created_at: datetime
    title: Optional[str] = None
    updated_at: Optional[datetime] = None
```

## Logic Flow

### create(user_id, chat_id=None)
```
1. IF chat_id is None:
     chat_id = generate_uuid()
2. INSERT INTO chats (id, user_id, created_at) VALUES (chat_id, user_id, NOW())
3. RETURN Chat(id=chat_id, user_id=user_id, created_at=NOW())
```

### get_by_id(chat_id)
```
1. SELECT * FROM chats WHERE id = chat_id
2. IF row exists:
     RETURN Chat from row
3. ELSE:
     RETURN None
```

### get_by_user(user_id)
```
1. SELECT * FROM chats WHERE user_id = user_id ORDER BY created_at DESC
2. RETURN List[Chat] from rows
```

### delete(chat_id)
```
1. DELETE FROM chats WHERE id = chat_id
2. RETURN affected_rows > 0
```

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| sql/V2__create_chats_table.sql | Create | Flyway migration |
| backend/models/chat.py | Create | Chat dataclass |
| backend/repositories/chat_repository.py | Create | IChatRepository + MySQLChatRepository |
| tests/unit/test_chat_repository.py | Create | Unit tests |

## BDD Scenarios (3)

### Scenario 1: Create chat for authenticated user
```gherkin
Given a user "alice" exists in the database
When alice creates a new chat
Then a chat record is created with alice's user_id
And the chat has a valid UUID and timestamp
```

### Scenario 2: Retrieve chat by ID
```gherkin
Given a user "bob" has an existing chat "chat-123"
When I query for chat "chat-123"
Then I receive the chat with correct user_id and metadata
```

### Scenario 3: User isolation - cannot see other users' chats
```gherkin
Given user "alice" has chat "chat-a"
And user "bob" has chat "chat-b"
When alice queries her chats
Then she sees only "chat-a"
And she does not see "chat-b"
```

## Context Budget

| Metric | Estimate |
|--------|----------|
| Files to read | 2 (~100 lines) - existing V1 migration, database.py patterns |
| New code to write | ~80 lines (migration + model + repository) |
| Test code to write | ~60 lines |
| **Estimated context usage** | **15%** |

## Dependencies
- V1 migration (users table) must exist
- MySQL connection pool from existing database.py

## Acceptance Criteria
- [ ] V2 migration creates chats table with FK to users
- [ ] Chat CRUD operations work via repository
- [ ] User isolation enforced at query level
- [ ] All 3 BDD scenarios pass
