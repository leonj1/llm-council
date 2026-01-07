# DRAFT: Conversation Ownership Validation

## Task Reference
**Active Stack Item**: 1.1 Conversation Ownership Validation
**Root Request**: "...Add user_id to conversation storage...Validate ownership in GET /api/conversations/{id}...only if it belongs to the authenticated user...Filter conversation list by authenticated user"

**Scope**: Backend-only. Adds ownership tracking and validation to conversation endpoints.

---

## Interfaces Needed

### ISessionUser
```python
# Extract authenticated user from session cookie
class ISessionUser(Protocol):
    def get_user_id(self, session_id: str) -> str | None:
        """Returns user_id if session valid, None otherwise"""
        ...
```

### IOwnershipValidator
```python
# Validate resource ownership
class IOwnershipValidator(Protocol):
    def validate(self, user_id: str, conversation_id: str) -> bool:
        """Returns True if user owns conversation"""
        ...
```

---

## Data Models

### Conversation (extended)
```python
class Conversation(BaseModel):
    id: str
    created_at: str
    user_id: str        # NEW: owner's user_id
    messages: list[Message]
```

### OwnershipError
```python
class OwnershipError(HTTPException):
    """403 Forbidden - user doesn't own this resource"""
    def __init__(self):
        super().__init__(status_code=403, detail="Access denied")
```

---

## Logic Flow

### 1. get_current_user Dependency
```
FUNCTION get_current_user(request: Request) -> str:
    session_id = request.cookies.get("session_id")
    IF NOT session_id:
        RAISE HTTPException(401, "Not authenticated")
    IF session_id NOT IN sessions:
        RAISE HTTPException(401, "Invalid session")
    RETURN sessions[session_id]["user_id"]
```

### 2. GET /api/conversations/{id} (ownership check)
```
ENDPOINT GET /api/conversations/{id}:
    user_id = Depends(get_current_user)
    conversation = storage.get(id)
    IF NOT conversation:
        RAISE HTTPException(404, "Not found")
    IF conversation.user_id != user_id:
        RAISE HTTPException(403, "Access denied")
    RETURN conversation
```

### 3. GET /api/conversations (filtered by user)
```
ENDPOINT GET /api/conversations:
    user_id = Depends(get_current_user)
    conversations = storage.get_all_by_user(user_id)
    RETURN conversations
```

### 4. DELETE /api/conversations/{id} (ownership check)
```
ENDPOINT DELETE /api/conversations/{id}:
    user_id = Depends(get_current_user)
    conversation = storage.get(id)
    IF NOT conversation:
        RAISE HTTPException(404, "Not found")
    IF conversation.user_id != user_id:
        RAISE HTTPException(403, "Access denied")
    storage.delete(id)
    RETURN {"status": "deleted"}
```

### 5. POST /api/conversations (set owner on create)
```
ENDPOINT POST /api/conversations:
    user_id = Depends(get_current_user)
    conversation = Conversation(
        id=generate_id(),
        created_at=now(),
        user_id=user_id,      # Set owner
        messages=[]
    )
    storage.save(conversation)
    RETURN conversation
```

### 6. Storage Layer (new method)
```
FUNCTION get_all_by_user(user_id: str) -> list[Conversation]:
    all_convs = load_all_conversations()
    RETURN [c for c in all_convs IF c.user_id == user_id]
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `backend/main.py` | Add get_current_user dependency, ownership checks on endpoints |
| `backend/storage.py` | Add user_id field, add get_all_by_user method |

---

## Context Budget

| Category | Count | Lines Est |
|----------|-------|-----------|
| Files to read | 2 | ~300 lines |
| New code to write | ~60 | lines |
| Test code to write | ~80 | lines |
| **Estimated context usage** | **15%** | |

---

## Error Handling Matrix

| Scenario | HTTP Status | Response |
|----------|-------------|----------|
| Valid session, owns conversation | 200 | Return conversation |
| No session cookie | 401 | "Not authenticated" |
| Invalid session | 401 | "Invalid session" |
| Conversation not found | 404 | "Not found" |
| Conversation owned by other user | 403 | "Access denied" |

---

## Acceptance Criteria

1. GET /api/conversations/{id} returns 403 if conversation.user_id != authenticated user
2. GET /api/conversations returns only conversations where user_id == authenticated user
3. DELETE /api/conversations/{id} returns 403 if not owner
4. POST /api/conversations sets user_id to authenticated user on creation
5. All endpoints return 401 if no valid session
