# BDD Specification: Chats Table Schema

## Overview
Create the foundational `chats` table with user association via foreign key to enable user-scoped chat persistence. This is sub-task 1.1 of the User Chat Persistence feature.

## User Stories
- As an authenticated user, I want my chats to be stored with my user identity so that my chats are persisted and isolated from other users

## Root Request Trace
- "Creating database tables for chats...linked to users"
- "user_id foreign key to associate chats with authenticated users"

## Feature Files
| Feature File | Scenarios | Coverage |
|--------------|-----------|----------|
| chats-table-schema.feature | 3 | Happy path, user isolation, list retrieval |

## Scenarios Summary

### chats-table-schema.feature
1. **User creates a chat and retrieves it** - Validates chat creation with user association, unique ID, and timestamp
2. **User cannot see another user's chats** - Validates user isolation at the data layer
3. **User retrieves their filtered chat list** - Validates filtered retrieval returns only user's own chats

## Acceptance Criteria
- [ ] User can create a chat that is associated with their user identity
- [ ] Created chat has a unique identifier and creation timestamp
- [ ] User can retrieve their own chat list
- [ ] User cannot see chats belonging to other users
- [ ] Chat list retrieval filters by user identity

## Dependencies
- V1 migration (users table) must exist
- Database connection available

## Next Steps
After these scenarios pass, proceed to:
- Sub-task 1.2: Messages Table Schema
