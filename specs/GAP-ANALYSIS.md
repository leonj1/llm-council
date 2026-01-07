# Gap Analysis: Conversation Ownership Validation

## Analysis Date: 2026-01-06

## Executive Summary
Add ownership tracking and validation to conversation endpoints. User must only access their own conversations. Existing auth patterns (sessions, get_current_user) can be reused. Storage layer needs user_id field.

## Root Request Trace
> "Add user_id to conversation storage", "Validate ownership in GET /api/conversations/{id}", "Filter conversation list by authenticated user"

## Existing Code to Reuse

### 1. Authentication Layer (`backend/auth.py`)
| Component | Purpose | Reuse |
|-----------|---------|-------|
| `sessions: dict` | In-memory session store | Direct reuse |
| `get_current_user()` | Extract user from session cookie | Convert to dependency |
| `@router.get("/me")` | Returns user info from session | Pattern for auth checks |

**Pattern**: Session cookie `session_id` maps to user dict in `sessions`

### 2. Database Layer (`backend/database.py`)
| Function | Purpose | Reuse |
|----------|---------|-------|
| `get_chat_by_id()` | Returns chat with `user_id` | Pattern for ownership check |
| `get_chats_by_user_id()` | Filter by user | Pattern for list filtering |
| `create_chat(user_id)` | Associates chat with user | Pattern for creation |

### 3. Storage Layer (`backend/storage.py`)
| Function | Purpose | Modification Needed |
|----------|---------|---------------------|
| `create_conversation()` | Creates new conversation | Add `user_id` param |
| `get_conversation()` | Load single conversation | No change (check ownership in main.py) |
| `list_conversations()` | List all conversations | Add `user_id` filter param |

## Similar Patterns Already Implemented

| Existing Pattern | New Equivalent |
|------------------|----------------|
| `get_chats_by_user_id(user_id)` | `list_conversations(user_id)` |
| `get_chat_by_id() -> {user_id}` | `get_conversation() -> {user_id}` |
| `auth.get_current_user()` | FastAPI Dependency for endpoints |

## Code Needing Refactoring

**None** - Extend existing patterns, no breaking changes

## New Components to Build

### 1. Auth Dependency (`backend/auth.py`)
```python
from fastapi import Depends, Request

async def require_auth(request: Request) -> dict:
    """FastAPI dependency for authenticated endpoints."""
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return sessions[session_id]
```

### 2. Storage Modifications (`backend/storage.py`)
| Change | Description |
|--------|-------------|
| `create_conversation(id, type, user_id)` | Add user_id to conversation dict |
| `list_conversations(user_id)` | Filter by user_id |
| Conversation JSON | Add `user_id` field |

### 3. Endpoint Modifications (`backend/main.py`)
| Endpoint | Change |
|----------|--------|
| `POST /api/conversations` | Inject auth, pass user_id to storage |
| `GET /api/conversations` | Inject auth, filter by user_id |
| `GET /api/conversations/{id}` | Inject auth, verify ownership (403 if mismatch) |
| `DELETE /api/conversations/{id}` | Inject auth, verify ownership |
| `POST /api/conversations/{id}/message` | Inject auth, verify ownership |

### 4. Error Responses
| Condition | HTTP Status | Response |
|-----------|-------------|----------|
| No session cookie | 401 | "Not authenticated" |
| Invalid session | 401 | "Not authenticated" |
| Conversation not found | 404 | "Conversation not found" |
| User doesn't own conversation | 403 | "Access denied" |

## Refactoring Decision

**Refactoring Needed**: No
**Scope**: N/A
**Risk**: N/A

## GO Signal

**STATUS: GO**

Rationale:
1. No refactoring required
2. Extend auth.py with FastAPI dependency
3. Add user_id to storage.py functions
4. Add auth checks to main.py endpoints
5. All patterns already exist in codebase

## Implementation Order
1. Add `require_auth` dependency to auth.py
2. Modify storage.py to include user_id
3. Update main.py endpoints with auth + ownership checks
4. Write tests for all 6 BDD scenarios
