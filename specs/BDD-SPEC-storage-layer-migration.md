# BDD Specification: Storage Layer Migration

## Overview

This specification defines the behavior for migrating chat persistence from JSON file storage (`storage.py`) to MySQL database storage (`database.py`). The new `chat_storage.py` module wraps database operations with user authorization and provides a consistent interface for chat and message management.

## User Stories

- As a user of the LLM Council application, I want my chats to be created and stored persistently so that I can access them across sessions
- As a user, I want to retrieve my stored chats so that I can continue previous conversations
- As a user, I want my chats to be private and isolated from other users so that my conversations remain confidential
- As a user, I want to store and retrieve messages in my chats so that my conversation history is preserved
- As a user, I want to delete my chats so that I can manage my conversation history
- As a user, I want the deliberation stage data to be fully preserved so that I can review the complete council process later

## Feature Files

| Feature File | Scenarios | Coverage |
|--------------|-----------|----------|
| chat-storage-creation.feature | 4 | Happy path, chat types, error handling |
| chat-storage-retrieval.feature | 4 | Get by ID, list chats, not found, empty list |
| chat-storage-user-isolation.feature | 4 | Cross-user access prevention |
| chat-storage-messages.feature | 5 | User/assistant messages, retrieval, errors |
| chat-storage-deletion.feature | 4 | Delete, cascade, verification |
| chat-storage-stage-data.feature | 5 | Stage 1/2/3 persistence, nested structures |

## Scenarios Summary

### chat-storage-creation.feature
1. User creates a new chat successfully
2. User creates a council-type chat
3. User creates a movie script chat
4. Chat creation fails when storage is unavailable

### chat-storage-retrieval.feature
1. User retrieves their own chat by identifier
2. User retrieves a chat that does not exist
3. User lists all their chats
4. User with no chats lists their chats

### chat-storage-user-isolation.feature
1. User cannot retrieve another user's chat
2. User cannot see another user's chats in their list
3. User cannot add messages to another user's chat
4. User cannot delete another user's chat

### chat-storage-messages.feature
1. User message is added to chat
2. Assistant message with stage data is added to chat
3. User retrieves all messages from a chat
4. User retrieves messages from empty chat
5. Adding message to non-existent chat fails

### chat-storage-deletion.feature
1. User deletes their own chat
2. User attempts to delete a non-existent chat
3. Deleted chat is no longer retrievable
4. Deleted chat no longer appears in chat list

### chat-storage-stage-data.feature
1. Stage one model responses are preserved
2. Stage two rankings are preserved
3. Stage three synthesis is preserved
4. All stages are retrieved together
5. Stage data with complex nested structures is preserved

## Acceptance Criteria

### Chat Creation
- Chats are saved to MySQL via database.py
- Each chat has a unique UUID identifier
- Chats are associated with a user_id
- Default title is "New Conversation"
- Chat type can be "council" or "movie_script"
- Returns None when database unavailable

### Chat Retrieval
- Get chat by ID returns chat with user association and timestamp
- Returns None for non-existent chat IDs
- List chats returns all chats for requesting user only
- List includes title, type, and message_count
- Results ordered by creation time (newest first)
- Empty list returned when user has no chats

### User Isolation
- Users cannot access other users' chats
- Cross-user retrieval returns None (not error)
- Cross-user message addition fails with authorization error
- Cross-user deletion returns failure indicator
- List only shows chats owned by requesting user

### Message Persistence
- User messages saved with role "user" and content
- Assistant messages saved with role "assistant" and stage data
- Stage 1, 2, 3 data preserved as JSON
- Messages retrievable in chronological order
- Empty list returned for chat with no messages
- Adding to non-existent chat returns failure

### Chat Deletion
- Delete removes chat and all messages (cascade)
- Returns success indicator on successful delete
- Returns failure indicator for non-existent chat
- Deleted chat not retrievable afterward
- Deleted chat not in list afterward

### Stage Data Integrity
- Stage 1: Model responses with identifiers preserved
- Stage 2: Ranking evaluations and parsed rankings preserved
- Stage 3: Synthesized response and chairman output preserved
- Complex nested structures preserved without corruption
- All stages retrievable together in single message

## Schema Mapping

| storage.py (JSON) | database.py (MySQL) | Notes |
|-------------------|---------------------|-------|
| conversation_id | chat_id | Renamed |
| messages[] array | messages table | Separate table |
| message.stage1 | stage1_data column | JSON serialized |
| message.stage2 | stage2_data column | JSON serialized |
| message.stage3 | stage3_data column | JSON serialized |

## Dependencies

- `backend/database.py` - Existing MySQL operations
- `backend/storage.py` - Kept for backward compatibility (not modified)

## Files to Create

| File | Purpose |
|------|---------|
| backend/chat_storage.py | MySQL-backed storage with user authorization |
| backend/tests/test_chat_storage.py | Unit tests for chat_storage module |

## Ready For

- **gherkin-to-test** agent: Convert scenarios to test prompts
- **test-creator** agent: Write pytest tests from Gherkin
- **coder** agent: Implement chat_storage.py to pass tests
