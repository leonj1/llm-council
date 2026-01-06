# BDD Specification: User Chat Persistence

## Overview
Implement database persistence for user chats and messages, replacing JSON file storage with MySQL. Chats are associated with authenticated users via foreign key, and authorization checks ensure users can only access their own data.

## User Stories
- As an authenticated user, I want my chats and LLM responses to be persisted in the database so that I can access my conversation history across sessions and devices

## Feature Files
| Feature File | Scenarios | Coverage |
|--------------|-----------|----------|
| user-chat-persistence.feature | 14 | Happy paths, edge cases, authorization |

## Scenarios Summary

### user-chat-persistence.feature

#### Chat Creation and Retrieval (2 scenarios)
1. **User creates a chat and retrieves it from the database** - Verifies chat creation persists with user_id, unique ID, and timestamp
2. **User's chat is not returned when another user queries the database** - Ensures user isolation at list level

#### Query Submission and Retrieval (1 scenario)
3. **User submits a query and retrieves it from the database** - Verifies user message content and timestamp persistence

#### LLM Response Retrieval (3 scenarios)
4. **Stage 1 LLM responses are retrieved from the database** - Verifies Stage 1 data with model identifiers and content
5. **Stage 2 rankings are retrieved from the database** - Verifies Stage 2 rankings with evaluating models and parsed order
6. **Stage 3 synthesis is retrieved from the database** - Verifies Stage 3 chairman synthesis with model ID and content

#### Complete Conversation Retrieval (1 scenario)
7. **Multiple exchanges are retrieved from the database in order** - Verifies message ordering across multiple query/response cycles

#### Chat List Retrieval (2 scenarios)
8. **User retrieves all their chats with metadata from the database** - Verifies chat list with title, timestamp, message count
9. **New user has empty chat list** - Edge case for users with no chats

#### Chat Management (2 scenarios)
10. **User deletes their own chat** - Verifies chat and message deletion
11. **User cannot delete another user's chat** - Authorization check for delete operation

#### Session Persistence Verification (1 scenario)
12. **User retrieves same chat data after re-authentication** - Verifies data survives session logout/login

#### Authorization - Data Isolation (2 scenarios)
13. **Unauthenticated request returns no user chats** - Returns 401 for no session
14. **User cannot fetch another user's chat data by ID** - Returns 403 for cross-user access

## Acceptance Criteria

### Chat Persistence
- [ ] Chats are stored in MySQL with unique UUID identifiers
- [ ] Chats have user_id foreign key linking to authenticated user
- [ ] Chats have creation timestamp
- [ ] Chat titles are stored and retrievable

### Message Persistence
- [ ] User messages store content and timestamp
- [ ] Assistant messages store Stage 1 JSON (multiple model responses)
- [ ] Assistant messages store Stage 2 JSON (rankings with parsed order)
- [ ] Assistant messages store Stage 3 JSON (chairman synthesis)
- [ ] Messages maintain chronological order

### Authorization
- [ ] Unauthenticated requests return 401
- [ ] Cross-user chat access returns 403
- [ ] Cross-user delete attempts return 403
- [ ] Users only see their own chats in list
- [ ] Users only access their own messages

### Data Integrity
- [ ] Data survives session logout/login
- [ ] Deleting chat removes associated messages
- [ ] New users have empty (not null) chat list

## Dependencies
- MySQL database with Flyway migrations
- Existing users table (V1)
- Session-based authentication
- mysql-connector-python library

## Traces to Root Request
| Scenario | Root Request Term |
|----------|-------------------|
| Chat creation/retrieval | "database tables for chats" |
| Message persistence | "database tables for messages" |
| Stage 1/2/3 retrieval | "LLM responses persisted and retrievable" |
| User isolation | "filter chats by authenticated user" |
| Authorization checks | "users can only access their own chats" |
| Session persistence | "MySQL instead of JSON files" |
