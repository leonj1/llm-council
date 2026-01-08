# Architect's Digest
> Status: In Progress

## Root Request
"Add a collapse icon to each stage (stage 1, stage 2, etc.) that toggles collapse/expand of just the selected stage"

## Active Stack
1. Add Stage Collapse Icons (Decomposed)

### Decomposition Justification for Task 1
| Sub-Task | Traces To Root Term | Because |
|----------|---------------------|---------|
| 1.1 Create shared CollapseIcon component + CSS | "collapse icon" | Reusable icon component for all stages |
| 1.2 Add collapse to Stage1 and Stage2 | "each stage" + "toggles collapse/expand" | Apply toggle to first two stages |
| 1.3 Add collapse to Stage3 and Stage4 | "each stage" + "toggles collapse/expand" | Apply toggle to remaining stages |

   1.1 Create shared CollapseIcon component + CSS (In Progress)
   1.2 Add collapse to Stage1 and Stage2 (Pending)
   1.3 Add collapse to Stage3 and Stage4 (Pending)

---

## Completed
- [x] Create landing page with Hello World and routing
- [x] Prereq: Database Schema - Chats Table (user chat persistence)
- [x] Prereq: Database Schema - Messages Table (user chat persistence)
- [x] 1.1 Conversation Ownership Validation
    - Added user_id field to conversation storage
    - Added require_auth dependency for authentication
    - Validate ownership in GET /api/conversations/{id} (403 if not owner)
    - Filter GET /api/conversations by authenticated user_id
    - DELETE endpoint checks ownership
    - 8 tests passing in test_conversation_ownership.py
- [x] 1.2 Chat URL Routing
    - Added /chat/:conversationId route to main.jsx
    - App.jsx reads useParams(), syncs with currentConversationId
    - Handles 403/404 errors with redirect to /chat
    - Error banner UI with dismiss button
- [x] Toggle Collapse/Expand Chat Messages
    - Chevron icon on each message
    - Collapsed state shows truncated preview
    - State managed per-message in ChatInterface.jsx
- [x] Wire MySQL Persistence
    - Replaced storage.py calls with database.py in main.py
