# Architect's Digest
> Status: Planning

## Root Request
"Wire main.py to use database.py for MySQL persistence instead of storage.py for JSON file storage. Replace storage.create_conversation() with database.create_chat(), storage.add_user_message()/add_assistant_message() with database.create_message(). Handle schema differences: storage uses conversation_id vs database uses chat_id, storage stores full message object vs database has separate columns for content, stage1_data, stage2_data, stage3_data."

## Active Stack
1. Wire MySQL Persistence (Pending)

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
