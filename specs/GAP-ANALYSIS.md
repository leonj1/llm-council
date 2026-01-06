# Gap Analysis: Messages Table Schema

## Analysis Date: 2026-01-06

## Executive Summary
Extend database layer to support messages table with chat association and JSON stage data. All existing patterns can be reused. V2 (chats table) dependency is complete.

## Root Request Trace
> "Creating database tables for...messages", "Stage 1, 2, 3...persisted and retrievable from the database"

## Existing Code to Reuse

### 1. Database Layer (`backend/database.py`)
| Function | Purpose | Reuse |
|----------|---------|-------|
| `get_connection()` | MySQL connection factory | Direct reuse |
| `get_db_cursor()` | Context manager with auto-commit/rollback | Direct reuse |
| `get_user_by_email()` | Find user by email | Use in tests |
| `create_chat()` | Create chat for user | Use in tests |
| `get_chat_by_id()` | Fetch single chat | Use for validation |

**Pattern**: All functions return `Optional[dict]` with dictionary cursor

### 2. Existing Schema
| Migration | Table | Status |
|-----------|-------|--------|
| V1 | users | Complete |
| V2 | chats | Complete |

### 3. V2 Schema (`sql/V2__create_chats_table.sql`)
| Element | Value | Relevance |
|---------|-------|-----------|
| `chats.id` | VARCHAR(36) PRIMARY KEY | Foreign key target for messages |
| `ON DELETE CASCADE` | FK pattern | Reuse for messages->chats |
| Engine | InnoDB | Required for FK |
| Charset | utf8mb4 | Consistency |

## Similar Patterns Already Implemented

| Existing Pattern | New (Messages) Equivalent |
|------------------|---------------------------|
| `create_chat(user_id)` | `create_message(chat_id, role, content, stage1, stage2, stage3)` |
| `get_chat_by_id(chat_id)` | `get_message_by_id(message_id)` |
| `get_chats_by_user_id(user_id)` | `get_messages_by_chat_id(chat_id)` |

## Code Needing Refactoring

**None** - existing code follows standards and can be extended directly

## New Components to Build

### 1. Flyway Migration: `sql/V3__create_messages_table.sql`
```sql
CREATE TABLE IF NOT EXISTS messages (
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

### 2. Repository Functions (add to `backend/database.py`)
| Function | Signature | Purpose |
|----------|-----------|---------|
| `create_message` | `(chat_id, role, content, stage1, stage2, stage3) -> Optional[dict]` | Create message with stage data |
| `get_messages_by_chat_id` | `(chat_id: str) -> List[dict]` | List messages chronologically |
| `get_message_by_id` | `(message_id: int) -> Optional[dict]` | Fetch single message |
| `delete_chat` | `(chat_id: str) -> bool` | Delete chat (cascade delete test) |

## JSON Handling Notes

- MySQL JSON columns require proper serialization
- Use `json.dumps()` for Python dict -> JSON string when inserting
- mysql.connector may auto-deserialize JSON columns to dict
- Stage data fields (stage1_data, stage2_data, stage3_data) are nullable

## Refactoring Decision

**Refactoring Needed**: No
**Scope**: N/A
**Risk**: N/A

## GO Signal

**STATUS: GO**

Rationale:
1. No refactoring required
2. Extend existing patterns in database.py
3. New Flyway migration V3 for messages table
4. All dependencies (V1 users, V2 chats) already exist
5. Established patterns for FK with cascade delete

## Implementation Order
1. Create V3 migration for messages table
2. Add repository functions to database.py
3. Write tests validating all 5 scenarios
