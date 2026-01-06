# Gap Analysis: Chats Table Schema

## Analysis Date: 2026-01-06

## Executive Summary
Extend database layer to support chats table with user association. All existing patterns can be reused.

## Existing Code to Reuse

### 1. Database Layer (`backend/database.py`)
| Function | Purpose | Reuse |
|----------|---------|-------|
| `get_connection()` | MySQL connection factory | Direct reuse |
| `get_db_cursor()` | Context manager with auto-commit/rollback | Direct reuse |
| `get_user_by_email()` | Find user by email | Use in tests |
| `get_user_by_id()` | Find user by ID | Use in tests |

**Pattern**: All functions return `Optional[dict]` with dictionary cursor

### 2. Existing Schema (`sql/V1__create_users_table.sql`)
| Element | Value | Relevance |
|---------|-------|-----------|
| `users.id` | INT PRIMARY KEY | Foreign key target |
| Timestamps | `created_at`, `updated_at` | Pattern to follow |
| Engine | InnoDB | Required for FK |
| Charset | utf8mb4 | Consistency |

## Similar Patterns Already Implemented

| Existing Pattern | New (Chats) Equivalent |
|------------------|------------------------|
| `upsert_user(google_id, email, ...)` | `create_chat(user_id)` |
| `get_user_by_id(user_id)` | `get_chat_by_id(chat_id)` |
| `get_user_by_email(email)` | `get_chats_by_user_id(user_id)` |

## Code Needing Refactoring

**None** - existing code follows standards and can be extended directly

## New Components to Build

### 1. Flyway Migration: `sql/V2__create_chats_table.sql`
```sql
CREATE TABLE chats (
    id VARCHAR(36) PRIMARY KEY,  -- UUID
    user_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id)
);
```

### 2. Repository Functions (add to `backend/database.py`)
| Function | Signature | Purpose |
|----------|-----------|---------|
| `create_chat` | `(user_id: int) -> Optional[dict]` | Create chat for user |
| `get_chat_by_id` | `(chat_id: str) -> Optional[dict]` | Fetch single chat |
| `get_chats_by_user_id` | `(user_id: int) -> List[dict]` | List user's chats |

## Refactoring Decision

**Refactoring Needed**: No
**Scope**: N/A
**Risk**: N/A

## GO Signal

**STATUS: GO**

Rationale:
1. No refactoring required
2. Extend existing patterns in database.py
3. New Flyway migration V2 for chats table
4. All dependencies (users table) already exist

## Implementation Order
1. Create V2 migration for chats table
2. Add repository functions to database.py
3. Write tests validating all 3 scenarios
