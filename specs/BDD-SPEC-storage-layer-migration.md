# BDD Specification: Storage Layer Migration

## Overview

Wire main.py to use database.py for MySQL persistence instead of storage.py for JSON file storage. This spec covers the direct replacement of storage function calls with database function calls, including schema translation between API conventions (conversation_id) and database conventions (chat_id).

## User Stories

- As a user of the LLM Council, I want my conversations stored in the database so that my chat history persists reliably

## Feature Files

| Feature File | Scenarios | Coverage |
|--------------|-----------|----------|
| main-database-wiring.feature | 4 | Create, user message, assistant message, retrieve |

## Scenarios Summary

### main-database-wiring.feature

1. **Create conversation stores to database**
   - Validates that POST /api/conversations uses database.create_chat()
   - Response contains conversation identifier (translated from chat_id)

2. **Add user message stores with user role**
   - Validates that user messages are stored via database.create_message()
   - Role is "user", content is the message text
   - No stage data for user messages (all stage columns null)

3. **Add assistant message stores stage data separately**
   - Validates that assistant messages unpack stage data into separate columns
   - stage1_data, stage2_data, stage3_data stored in their respective columns
   - Content field contains the final synthesized answer from stage3

4. **Get conversation retrieves from database**
   - Validates that GET /api/conversations/{id} uses database.get_chat_by_id()
   - Messages retrieved via database.get_messages_by_chat_id()
   - Response uses "id" field (API convention, not "chat_id")

## Acceptance Criteria

### Create Conversation
- [ ] database.create_chat() is called instead of storage.create_conversation()
- [ ] Response translates chat_id to conversation_id for API compatibility

### Add User Message
- [ ] database.create_message() is called with role="user"
- [ ] content parameter contains the user's message
- [ ] stage1_data, stage2_data, stage3_data are all None

### Add Assistant Message
- [ ] database.create_message() is called with role="assistant"
- [ ] stage1_data contains the stage 1 model responses
- [ ] stage2_data contains the stage 2 rankings
- [ ] stage3_data contains the stage 3 synthesis
- [ ] content contains stage3["response"] or equivalent final answer

### Get Conversation
- [ ] database.get_chat_by_id() is called instead of storage.get_conversation()
- [ ] database.get_messages_by_chat_id() retrieves all messages
- [ ] Response format matches existing API contract (id, not chat_id)

## Schema Translation Reference

| API/Storage Convention | Database Convention |
|------------------------|---------------------|
| conversation_id | chat_id |
| conversation | chat |
| message["content"] | content param |
| message["stage1"] | stage1_data param |
| message["stage2"] | stage2_data param |
| message["stage3"] | stage3_data param |

## What This Spec Does NOT Include

Per user request, the following are explicitly excluded:
- User isolation logic
- Chat deletion
- Chat types/titles
- Error handling beyond existing

## Ready For

- gherkin-to-test agent
