# BDD Specification: Chat URL Routing (Frontend)

## Overview

This specification covers the frontend implementation of chat URL routing:
1. React Router route for `/chat/:conversationId`
2. URL synchronization with conversation selection
3. Browser history navigation support
4. Auth guards and error handling

## Sub-Task Scope

**From Root Request:** Chat URL Routing (Frontend)

**Implementation Focus:**
- Add React Router route for `/chat/:conversationId`
- Update `App.jsx` to read `conversationId` from URL params
- Update `Sidebar.jsx` to use `navigate()` instead of callback

## User Stories

- As an authenticated user, I want the URL to reflect the currently selected chat so that I can bookmark and share specific conversations
- As an authenticated user, I want to navigate directly to a conversation via URL so that I can quickly access bookmarked chats

## Feature Files

| Feature File | Scenarios | Coverage |
|--------------|-----------|----------|
| chat-url-routing.feature | 11 | URL navigation, browser history, edge cases, auth |

## Scenarios Summary

### chat-url-routing.feature

**Happy Paths (URL Navigation):**
1. URL updates when selecting a chat from sidebar
2. Navigate directly to a chat via URL
3. Create new conversation updates URL
4. Browser back button navigates chat history
5. Browser forward button navigates chat history

**Edge Cases:**
6. Navigate to base chat URL with no conversation selected
7. Navigate to URL for non-existent conversation
8. Conversation list filtered to current user only (backend-driven)

**Authentication/Authorization:**
9. Access denied when viewing another user's conversation
10. Unauthenticated user redirected from chat URL
11. Unauthenticated user redirected from base chat page

## Frontend Implementation Mapping

| Scenario | Component | Change Required |
|----------|-----------|-----------------|
| 1 | Sidebar.jsx | Use `navigate('/chat/{id}')` on selection |
| 2 | main.jsx, App.jsx | Add route param, use `useParams()` |
| 3 | App.jsx | `navigate('/chat/{newId}')` after create |
| 4-5 | React Router | Handled automatically with proper routing |
| 6 | App.jsx | Handle missing param gracefully |
| 7 | App.jsx | Handle 404 response, show error message |
| 8 | API layer | Backend filters (no frontend change) |
| 9 | App.jsx | Handle 403 response, redirect + message |
| 10-11 | main.jsx | ProtectedRoute wrapper or auth check |

## Acceptance Criteria

### URL Routing (Frontend)
- [ ] Route `/chat/:conversationId` defined in main.jsx
- [ ] App.jsx reads `conversationId` via `useParams()`
- [ ] Sidebar uses `navigate()` for conversation selection
- [ ] New conversation creation calls `navigate('/chat/{newId}')`
- [ ] Browser back/forward buttons work with chat navigation
- [ ] Base `/chat` URL shows no conversation selected

### Error Handling (Frontend)
- [ ] 404 response redirects to `/chat` with "Not found" message
- [ ] 403 response redirects to `/chat` with "Access denied" message
- [ ] Unauthenticated access redirects to `/` (landing page)

## Current State Analysis

**main.jsx:**
- Has `/chat` route but no `:conversationId` param
- Uses BrowserRouter with Routes

**App.jsx:**
- Uses `useState` for `currentConversationId`
- `handleSelectConversation(id)` sets state only
- No URL param reading

**Sidebar.jsx:**
- Uses `onSelectConversation` callback prop
- No direct navigation

## Error Handling Matrix

| API Response | Frontend Behavior |
|--------------|-------------------|
| 200 OK | Load and display conversation |
| 404 Not Found | Redirect to /chat, show "Not found" toast |
| 403 Forbidden | Redirect to /chat, show "Access denied" toast |
| 401 Unauthorized | Redirect to / (landing page) |

## Ready For

- gherkin-to-test agent
- test-creator agent
- coder agent
