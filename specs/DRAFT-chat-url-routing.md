# DRAFT: Chat URL Routing with Authentication

## Task Reference
**Active Stack Item**: 1.1 Frontend URL Routing (subset of "Chat URL Routing with Auth")

**Root Request**: "Implement chat URL routing where selecting a chat updates URL to /chat/{conversationId} and navigating to /chat/{conversationId} opens that specific chat only if it belongs to the authenticated user"

**Scope**: This spec covers the FULL feature (1.1-1.4) as they are tightly coupled. Frontend routing requires backend ownership validation to function correctly.

---

## Interfaces Needed

### Frontend Interfaces

```typescript
// IRouteParams - URL parameter extraction
interface IRouteParams {
  conversationId?: string;
}

// INavigationService - Abstraction for route navigation
interface INavigationService {
  navigateToChat(conversationId: string): void;
  navigateToNewChat(): void;
  getCurrentConversationId(): string | null;
}

// IChatLoader - Load chat by ID with auth
interface IChatLoader {
  loadConversation(conversationId: string): Promise<Conversation | null>;
  handleLoadError(error: Error, conversationId: string): void;
}
```

### Backend Interfaces

```typescript
// ISessionUser - Extract user from session cookie
interface ISessionUser {
  getUserId(sessionId: string): string | null;
}

// IOwnershipValidator - Verify resource ownership
interface IOwnershipValidator {
  validateOwnership(userId: string, conversationId: string): Promise<boolean>;
}

// IConversationFilter - Filter by user
interface IConversationFilter {
  getByUser(userId: string): Promise<Conversation[]>;
  getByIdAndUser(conversationId: string, userId: string): Promise<Conversation | null>;
}
```

---

## Data Models

### Frontend Models

```typescript
interface Conversation {
  id: string;
  created_at: string;
  user_id: string;        // NEW: ownership tracking
  messages: Message[];
}

interface Message {
  role: 'user' | 'assistant';
  content?: string;
  stage1?: Stage1Response;
  stage2?: Stage2Response;
  stage3?: Stage3Response;
}

interface ApiError {
  status: number;
  message: string;
}
```

### Backend Models (Pydantic)

```python
class ConversationResponse(BaseModel):
    id: str
    created_at: str
    user_id: str
    messages: list[MessageResponse]

class OwnershipError(Exception):
    """Raised when user attempts to access another user's resource"""
    status_code: int = 403
    detail: str = "Access denied: conversation belongs to another user"
```

---

## Logic Flow

### 1. Route Configuration (main.jsx)

```
CURRENT ROUTES:
  "/" -> LandingPage
  "/chat" -> App

ADD ROUTE:
  "/chat/:conversationId" -> App (same component, with URL param)

PSEUDOCODE:
  <Routes>
    <Route path="/" element={<LandingPage />} />
    <Route path="/chat" element={<App />} />
    <Route path="/chat/:conversationId" element={<App />} />  // NEW
  </Routes>
```

### 2. App.jsx URL Sync

```
ON MOUNT:
  conversationId = useParams().conversationId
  IF conversationId EXISTS:
    TRY:
      conversation = await api.getConversation(conversationId)
      setCurrentConversationId(conversationId)
      setConversations(prev => includeIfMissing(prev, conversation))
    CATCH 403:
      navigate('/chat')  // Redirect to chat home on forbidden
      showError("You don't have access to this conversation")
    CATCH 404:
      navigate('/chat')
      showError("Conversation not found")

ON SELECT CONVERSATION:
  setCurrentConversationId(id)
  navigate(`/chat/${id}`)  // NEW: Update URL

ON NEW CONVERSATION:
  newId = createConversation()
  navigate(`/chat/${newId}`)  // NEW: Navigate to new chat URL
```

### 3. Sidebar Navigation

```
CURRENT:
  onClick={onSelectConversation(conv.id)}

CHANGE TO:
  import { useNavigate } from 'react-router-dom'
  const navigate = useNavigate()

  onClick={() => navigate(`/chat/${conv.id}`)}

  // Remove onSelectConversation prop, App listens to URL changes instead
```

### 4. Backend Ownership Validation (main.py)

```
DEPENDENCY: get_current_user
  session_id = request.cookies.get("session_id")
  IF NOT session_id OR session_id NOT IN sessions:
    RAISE HTTPException(401, "Not authenticated")
  RETURN sessions[session_id]["user_id"]

GET /api/conversations/{id}:
  user_id = Depends(get_current_user)
  conversation = storage.get(id)
  IF NOT conversation:
    RAISE HTTPException(404)
  IF conversation.user_id != user_id:
    RAISE HTTPException(403, "Access denied")
  RETURN conversation

GET /api/conversations:
  user_id = Depends(get_current_user)
  conversations = storage.get_all_by_user(user_id)
  RETURN conversations
```

### 5. API Client Credentials (api.js)

```
CURRENT:
  fetch(url, { method, headers, body })

ADD credentials:
  fetch(url, {
    method,
    headers,
    body,
    credentials: 'include'  // Send cookies with requests
  })
```

---

## Error Handling Matrix

| Scenario | HTTP Status | Frontend Action |
|----------|-------------|-----------------|
| Valid conversation, owned by user | 200 | Load chat |
| Conversation not found | 404 | Redirect to /chat, toast "Not found" |
| Conversation owned by other user | 403 | Redirect to /chat, toast "Access denied" |
| Not authenticated | 401 | Redirect to "/" (landing) |
| Server error | 500 | Show error, stay on current page |

---

## Files to Modify

### Frontend
1. `frontend/src/main.jsx` - Add parameterized route
2. `frontend/src/App.jsx` - URL sync, useParams, useNavigate
3. `frontend/src/components/Sidebar.jsx` - Use navigate() for selection
4. `frontend/src/api.js` - Add credentials: 'include'

### Backend
1. `backend/main.py` - Add get_current_user dependency, ownership checks
2. `backend/storage.py` - Add get_by_user filter method

---

## Context Budget

| Category | Count | Lines Est |
|----------|-------|-----------|
| Files to read | 6 | ~600 lines |
| New code to write | ~120 | lines |
| Test code to write | ~150 | lines |
| **Estimated context usage** | **25%** | (Well under 60% threshold) |

---

## Security Considerations

1. **Session Cookie Validation**: Every protected endpoint must validate session
2. **Ownership Check**: NEVER return data without verifying user_id match
3. **No ID Enumeration**: 403 and 404 should have same timing to prevent probing
4. **CORS Credentials**: Ensure Access-Control-Allow-Credentials: true in CORS config

---

## Acceptance Criteria

1. Selecting a chat in sidebar updates URL to `/chat/{conversationId}`
2. Navigating directly to `/chat/{conversationId}` loads that chat
3. Navigating to another user's chat returns 403 and redirects to /chat
4. Conversation list only shows authenticated user's conversations
5. Browser back/forward buttons work correctly with chat selection
6. New conversation creation navigates to `/chat/{newId}`
