# BDD Specification: Chat URL Routing with Authentication

## Overview

This specification covers the chat URL routing feature that enables:
1. URL synchronization with selected conversations
2. Direct navigation to conversations via URL
3. Conversation ownership and access control

## User Stories

- As an authenticated user, I want the URL to reflect the currently selected chat so that I can bookmark and share specific conversations
- As an authenticated user, I want to navigate directly to a conversation via URL so that I can quickly access bookmarked chats
- As an authenticated user, I want my conversations to be private so that other users cannot access my chat history

## Feature Files

| Feature File | Scenarios | Coverage |
|--------------|-----------|----------|
| chat-url-routing.feature | 11 | URL navigation, browser history, edge cases, auth |
| conversation-ownership.feature | 6 | Ownership assignment, validation, error cases |

## Scenarios Summary

### chat-url-routing.feature

**Happy Paths:**
1. URL updates when selecting a chat from sidebar
2. Navigate directly to a chat via URL
3. Create new conversation updates URL
4. Browser back button navigates chat history
5. Browser forward button navigates chat history

**Edge Cases:**
6. Navigate to base chat URL with no conversation selected
7. Navigate to URL for non-existent conversation
8. Conversation list filtered to current user only

**Authentication/Authorization:**
9. Access denied when viewing another user's conversation
10. Unauthenticated user redirected from chat URL
11. Unauthenticated user redirected from base chat page

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

### URL Routing
- [ ] Selecting a chat in sidebar updates URL to `/chat/{conversationId}`
- [ ] Navigating directly to `/chat/{conversationId}` loads that chat
- [ ] New conversation creation navigates to `/chat/{newId}`
- [ ] Browser back/forward buttons work correctly with chat selection
- [ ] Base `/chat` URL shows no conversation selected

### Ownership & Access Control
- [ ] Navigating to another user's chat returns 403 and redirects to /chat
- [ ] Conversation list only shows authenticated user's conversations
- [ ] Non-existent conversation returns 404 and redirects to /chat
- [ ] Unauthenticated access redirects to landing page

### Data Model
- [ ] Conversations have `user_id` field for ownership tracking
- [ ] Backend validates ownership on all conversation endpoints

## Error Handling Matrix

| Scenario | Expected Behavior |
|----------|-------------------|
| Valid conversation, owned by user | Load chat |
| Conversation not found | Redirect to /chat, show "Not found" |
| Conversation owned by other user | Redirect to /chat, show "Access denied" |
| Not authenticated | Redirect to "/" (landing) |
