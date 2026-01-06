# Architect's Digest
> Status: In Progress

## Root Request
"Implement chat URL routing where selecting a chat updates URL to /chat/{conversationId} and navigating to /chat/{conversationId} opens that specific chat only if it belongs to the authenticated user. Requirements: 1) Add React Router route for /chat/:conversationId 2) Update App.jsx to read conversationId from URL params and navigate on selection 3) Update Sidebar to use navigate() 4) Add user_id to conversation storage 5) Validate ownership in GET /api/conversations/{id} 6) Filter conversation list by authenticated user"

## Active Stack
1. Chat URL Routing with Auth (Decomposed)

### Decomposition Justification for Task 1
| Sub-Task | Traces To Root Term | Because |
|----------|---------------------|---------|
| 1.1 Frontend URL routing | "Add React Router route for /chat/:conversationId", "Update App.jsx to read conversationId from URL params" | Enables URL-based chat selection |
| 1.2 Sidebar navigation | "Update Sidebar to use navigate()" | Syncs UI selection with URL changes |
| 1.3 Backend ownership validation | "Validate ownership in GET /api/conversations/{id}", "only if it belongs to the authenticated user" | Security: prevents unauthorized chat access |
| 1.4 Conversation list filtering | "Filter conversation list by authenticated user" | User isolation: only show user's own chats |

   1.1 Frontend URL Routing (In Progress)
       - Add /chat/:conversationId route to main.jsx
       - Update App.jsx to read useParams(), sync with currentConversationId
       - Handle direct URL navigation (load chat on mount if conversationId present)

   1.2 Sidebar Navigation (Pending)
       - Import useNavigate hook in Sidebar
       - Replace onSelectConversation callback with navigate('/chat/{id}')
       - Handle new conversation creation with navigation

   1.3 Backend Ownership Validation (Pending)
       - Add get_current_user dependency to extract user_id from session
       - Update GET /api/conversations/{id} to check chat.user_id == user_id
       - Return 403 Forbidden if not owner
       - Update DELETE endpoint similarly

   1.4 Conversation List Filtering (Pending)
       - Update GET /api/conversations to accept user_id filter
       - Require authentication, filter by session user_id
       - Return only user's own conversations

## Completed
- [x] Create landing page with Hello World and routing
- [x] 1.1 Database Schema - Chats Table (user chat persistence)
- [x] 1.2 Database Schema - Messages Table (user chat persistence)
