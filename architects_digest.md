# Architect's Digest
> Status: In Progress

## Root Request
"Implement user chat persistence in MySQL based on the BDD test in tests/bdd/user-chat-persistence.feature. The feature requires: 1) Creating database tables for chats and messages linked to users, 2) Updating storage.py to use MySQL instead of JSON files, 3) Adding user_id foreign key to associate chats with authenticated users, 4) Updating API endpoints to filter chats by authenticated user, 5) Ensuring all LLM responses (Stage 1, 2, 3) are persisted and retrievable from the database, 6) Authorization checks so users can only access their own chats."

## Active Stack
1. User Chat Persistence in MySQL (Decomposed)
   - BDD Test: /root/repo/tests/bdd/user-chat-persistence.feature

### Decomposition Justification for Task 1
| Sub-Task | Traces To Root Term | Because |
|----------|---------------------|---------|
| 1.1 Chats table schema | "Creating database tables for chats...linked to users", "user_id foreign key" | Foundation for chat persistence with user association |
| 1.2 Messages table schema | "Creating database tables for...messages", "Stage 1, 2, 3...persisted" | Stores conversation content including LLM stages |
| 1.3 Storage layer migration | "Updating storage.py to use MySQL instead of JSON files", "retrievable from database" | Replaces file-based storage with MySQL-backed functions |
| 1.4 API authorization | "filter chats by authenticated user", "Authorization checks so users can only access their own chats" | Endpoint security and user isolation |

   1.1 Database Schema - Chats Table (In Progress)
       - V2 migration for `chats` table with user_id FK
       - Basic CRUD for chats in database.py
       - Scenarios: Create chat, retrieve chat, user isolation (3)

   1.2 Database Schema - Messages Table (Pending)
       - V3 migration for `messages` table with chat_id FK
       - Message CRUD with stage1/2/3 JSON storage
       - Scenarios: Store/retrieve user msg, store/retrieve assistant msg (3)

   1.3 Storage Layer Migration (Pending)
       - chat_storage.py with MySQL-backed functions
       - Replace JSON file ops with MySQL calls
       - Scenarios: Query persistence, stage retrieval (4)

   1.4 API Authorization (Pending)
       - Update main.py endpoints for auth + user filtering
       - Authorization checks for chat access
       - Scenarios: Auth required, cross-user forbidden, delete auth (4)

## Completed
- [x] Create landing page with Hello World and routing
