# Gap Analysis: Chat URL Routing (Frontend)

## Analysis Date: 2026-01-06

## Executive Summary
Add URL routing for chat conversations. React Router already in use. Need to add route param, use `useParams()` and `navigate()` hooks. No refactoring needed.

## Root Request Trace
> "Add React Router route for /chat/:conversationId", "Update App.jsx to read conversationId from URL params", "Update Sidebar to use navigate()"

## Existing Code to Reuse

### 1. Router Setup (`frontend/src/main.jsx`)
| Component | Purpose | Reuse |
|-----------|---------|-------|
| `BrowserRouter` | History-based routing | Direct reuse |
| `Routes`, `Route` | Route definitions | Extend with param |
| `/chat` route | Chat app entry | Add `:conversationId` param |

### 2. App Component (`frontend/src/App.jsx`)
| Component | Purpose | Modification |
|-----------|---------|--------------|
| `useState(currentConversationId)` | Track selected conv | Sync with URL param |
| `handleSelectConversation(id)` | Selection handler | Add navigate() call |
| `handleNewConversation()` | Create new conv | Add navigate() call |
| `loadConversation(id)` | Fetch conv details | No change |

### 3. Sidebar (`frontend/src/components/Sidebar.jsx`)
| Component | Purpose | Modification |
|-----------|---------|--------------|
| `onSelectConversation(id)` | Callback on select | Replace with navigate() |
| Conversation list | Display convs | No change |

### 4. API Layer (`frontend/src/api.js`)
| Function | Purpose | Modification |
|----------|---------|--------------|
| `getConversation()` | Fetch by ID | Add error status handling |
| `listConversations()` | Fetch list | No change |
| `createConversation()` | Create new | No change |

## Similar Patterns Already Implemented

| Existing Pattern | New Equivalent |
|------------------|----------------|
| `<Route path="/chat">` | `<Route path="/chat/:conversationId?">` |
| `setCurrentConversationId(id)` | `navigate('/chat/${id}')` + `useParams()` |
| LandingPage standalone route | Chat route with optional param |

## Code Needing Refactoring

**None** - Extend existing patterns, no breaking changes

## New Components to Build

### 1. Route Parameter (`main.jsx`)
```jsx
<Route path="/chat" element={<App />} />
<Route path="/chat/:conversationId" element={<App />} />
```

### 2. URL Param Reading (`App.jsx`)
```jsx
import { useParams, useNavigate } from 'react-router-dom';

function App() {
  const { conversationId } = useParams();
  const navigate = useNavigate();

  // Sync URL param with state
  useEffect(() => {
    if (conversationId && conversationId !== currentConversationId) {
      setCurrentConversationId(conversationId);
    }
  }, [conversationId]);
}
```

### 3. Navigation on Selection (`App.jsx`)
```jsx
const handleSelectConversation = (id) => {
  navigate(`/chat/${id}`);
  if (isMobile) setShowChat(true);
};

const handleNewConversation = async (type) => {
  const newConv = await api.createConversation(type);
  // ...
  navigate(`/chat/${newConv.id}`);
};
```

### 4. Navigate in Sidebar (`Sidebar.jsx`)
```jsx
import { useNavigate } from 'react-router-dom';

export default function Sidebar({ /* ... */ }) {
  const navigate = useNavigate();

  const handleSelect = (id) => {
    navigate(`/chat/${id}`);
    // Mobile handling passed via prop if needed
  };
}
```

### 5. Error Handling (`App.jsx`)
```jsx
const loadConversation = async (id) => {
  try {
    const conv = await api.getConversation(id);
    setCurrentConversation(conv);
  } catch (error) {
    if (error.status === 404) {
      navigate('/chat');
      setErrorMessage('Conversation not found');
    } else if (error.status === 403) {
      navigate('/chat');
      setErrorMessage('Access denied');
    }
  }
};
```

### 6. API Error Enhancement (`api.js`)
```jsx
async getConversation(conversationId) {
  const response = await fetch(...);
  if (!response.ok) {
    const error = new Error('Failed to get conversation');
    error.status = response.status;
    throw error;
  }
  return response.json();
}
```

## Files to Modify

| File | Changes |
|------|---------|
| `main.jsx` | Add route with `:conversationId` param |
| `App.jsx` | Add useParams, useNavigate, sync URL with state |
| `Sidebar.jsx` | Use navigate() for selection |
| `api.js` | Add error.status to thrown errors |

## Refactoring Decision

**Refactoring Needed**: No
**Scope**: N/A
**Risk**: N/A

## GO Signal

**STATUS: GO**

Rationale:
1. No refactoring required
2. React Router already configured
3. Simple hook additions (useParams, useNavigate)
4. State sync pattern is straightforward
5. Browser history handled automatically by React Router

## Implementation Order
1. Update main.jsx with route parameter
2. Add useParams/useNavigate to App.jsx
3. Update handleSelectConversation/handleNewConversation to navigate
4. Update Sidebar.jsx to use navigate
5. Add error status handling to api.js
6. Add error toast/message display
