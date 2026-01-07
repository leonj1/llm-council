# BDD Specification: Conversation Ownership Validation

## Overview

This specification covers backend ownership tracking and validation for conversations, ensuring users can only access their own chat history.

## User Stories

- As an authenticated user, I want my conversations to be private to my account so that other users cannot access my chat history

## Feature Files

| Feature File | Scenarios | Coverage |
|--------------|-----------|----------|
| conversation-ownership.feature | 6 | Ownership assignment, validation, error cases |

## Scenarios Summary

### conversation-ownership.feature

**Ownership Assignment:**
1. New conversation is assigned to creating user

**Ownership Validation:**
2. Successfully retrieve my own conversation
3. Cannot retrieve conversation owned by another user
4. Cannot list conversations owned by other users

**Error Cases:**
5. Request non-existent conversation returns not found
6. Request conversation without authentication returns unauthorized

## Acceptance Criteria

### Ownership Assignment
- [ ] New conversations include `user_id` field set to creating user
- [ ] `user_id` persisted with conversation data

### Ownership Validation on Retrieval
- [ ] GET /api/conversations/{id} returns conversation if user owns it
- [ ] GET /api/conversations/{id} returns 403 if another user owns it
- [ ] GET /api/conversations/{id} returns 404 if conversation does not exist

### Conversation List Filtering
- [ ] GET /api/conversations returns only conversations owned by authenticated user
- [ ] Count matches user's actual conversation count

### Authentication Requirements
- [ ] All conversation endpoints require valid session
- [ ] Missing/invalid session returns 401 Unauthorized

## Error Handling Matrix

| Scenario | HTTP Status | Response |
|----------|-------------|----------|
| Valid session, owns conversation | 200 | Return conversation |
| No session cookie | 401 | "Not authenticated" |
| Invalid session | 401 | "Invalid session" |
| Conversation not found | 404 | "Not found" |
| Conversation owned by other user | 403 | "Access denied" |

## Data Model Changes

### Conversation (extended)
```
Conversation:
  id: string
  created_at: string
  user_id: string        # NEW: owner's user_id
  messages: list[Message]
```

## Files to Modify

| File | Changes |
|------|---------|
| `backend/main.py` | Add get_current_user dependency, ownership checks on endpoints |
| `backend/storage.py` | Add user_id field, add get_all_by_user method |
