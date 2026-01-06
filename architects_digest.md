# Architect's Digest
> Status: In Progress

## Root Request
"Implement chat URL routing where selecting a chat updates URL to /chat/{conversationId} and navigating to /chat/{conversationId} opens that specific chat only if it belongs to the authenticated user. Requirements: 1) Add React Router route for /chat/:conversationId 2) Update App.jsx to read conversationId from URL params and navigate on selection 3) Update Sidebar to use navigate() 4) Add user_id to conversation storage 5) Validate ownership in GET /api/conversations/{id} 6) Filter conversation list by authenticated user"

## Active Stack
1. Chat URL Routing with Auth (Decomposed)

### Decomposition Justification for Task 1
| Sub-Task | Traces To Root Term | Because |
|----------|---------------------|---------|
| 1.1 Conversation Ownership Validation | "Add user_id to conversation storage", "Validate ownership in GET /api/conversations/{id}", "only if it belongs to the authenticated user", "Filter conversation list by authenticated user" | Backend foundation: storage must track ownership before frontend can route to owned chats |
| 1.2 Chat URL Routing | "Add React Router route for /chat/:conversationId", "Update App.jsx to read conversationId from URL params", "Update Sidebar to use navigate()" | Frontend: URL-based chat selection (depends on 1.1 for ownership enforcement) |

   1.1 Conversation Ownership Validation (In Progress)
       - Add user_id field to conversation storage
       - Add get_current_user dependency for auth
       - Validate ownership in GET /api/conversations/{id} (return 403 if not owner)
       - Filter GET /api/conversations by authenticated user_id
       - Update DELETE endpoint to check ownership

   1.2 Chat URL Routing (Pending) [Blocked by 1.1]
       - Add /chat/:conversationId route to main.jsx
       - Update App.jsx to read useParams(), sync with currentConversationId
       - Update Sidebar to use navigate() instead of callback
       - Handle 403/404 errors with redirect to /chat

## Completed
- [x] Create landing page with Hello World and routing
- [x] 1.1 Database Schema - Chats Table (user chat persistence)
- [x] 1.2 Database Schema - Messages Table (user chat persistence)
