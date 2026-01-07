# Architect's Digest
> Status: Planning

## Root Request
"Add an icon on each chat message that allows the user to toggle collapsing and expanding the message. This is for lengthy messages that force scrolling."

## Active Stack
1. Toggle Collapse/Expand Chat Messages (DRAFT SPEC)

---

## DRAFT SPEC: Toggle Collapse/Expand Chat Messages

### Problem
Lengthy messages force excessive scrolling. Users need ability to collapse messages to see conversation overview.

### Solution Overview
Add collapsible wrapper around message content with chevron toggle icon. Collapsed state shows truncated preview (first ~100 chars). State managed per-message via React useState.

### Technical Approach

**1. State Management**
```jsx
// In ChatInterface.jsx
const [collapsedMessages, setCollapsedMessages] = useState({});
// Key: message index, Value: boolean (true = collapsed)

const toggleCollapse = (index) => {
  setCollapsedMessages(prev => ({
    ...prev,
    [index]: !prev[index]
  }));
};
```

**2. Inline SVG Chevron Icon (no dependencies)**
```jsx
const ChevronIcon = ({ isCollapsed }) => (
  <svg
    width="16"
    height="16"
    viewBox="0 0 16 16"
    style={{ transform: isCollapsed ? 'rotate(-90deg)' : 'rotate(0deg)', transition: 'transform 0.2s' }}
  >
    <path d="M4 6l4 4 4-4" stroke="currentColor" strokeWidth="2" fill="none"/>
  </svg>
);
```

**3. Message Wrapper Component**
Create `CollapsibleMessage` component or inline in ChatInterface:
- Wrap both user-message and assistant-message content
- Toggle button positioned in message-label row
- Collapsed: show truncated text with "..." and expand hint
- Expanded: show full content

**4. User Messages (simple)**
```jsx
<div className="user-message">
  <div className="message-label">
    <span>You</span>
    <button className="collapse-toggle" onClick={() => toggleCollapse(index)}>
      <ChevronIcon isCollapsed={collapsedMessages[index]} />
    </button>
  </div>
  <div className={`message-content ${collapsedMessages[index] ? 'collapsed' : ''}`}>
    {collapsedMessages[index] ? (
      <div className="collapsed-preview">
        {msg.content.slice(0, 100)}...
      </div>
    ) : (
      <div className="markdown-content">
        <Markdown>{msg.content}</Markdown>
      </div>
    )}
  </div>
</div>
```

**5. Assistant Messages (multi-stage)**
For assistant messages, collapse hides all stages (stage1-4):
```jsx
<div className="assistant-message">
  <div className="message-label">
    <span>{isMovieScript ? 'Movie Script Studio' : 'LLM Council'}</span>
    <button className="collapse-toggle" onClick={() => toggleCollapse(index)}>
      <ChevronIcon isCollapsed={collapsedMessages[index]} />
    </button>
  </div>
  {collapsedMessages[index] ? (
    <div className="collapsed-preview">
      [Response collapsed - click to expand]
    </div>
  ) : (
    <>
      {/* Existing stage1, stage2, stage3, stage4 rendering */}
    </>
  )}
</div>
```

**6. CSS Additions (ChatInterface.css)**
```css
.message-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.collapse-toggle {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  color: #666;
  display: flex;
  align-items: center;
}

.collapse-toggle:hover {
  color: #4a90e2;
}

.collapsed-preview {
  padding: 12px 16px;
  background: #f5f5f5;
  border-radius: 8px;
  color: #888;
  font-style: italic;
  cursor: pointer;
}

.message-content.collapsed {
  max-height: 60px;
  overflow: hidden;
}
```

### Files Modified
1. `/root/repo/frontend/src/components/ChatInterface.jsx` - Add state, toggle fn, update JSX
2. `/root/repo/frontend/src/components/ChatInterface.css` - Add collapse styles

### Edge Cases
- Empty messages: don't show collapse toggle
- Loading states: disable collapse during loading
- Very short messages (<100 chars): still show toggle for consistency

### Testing
- Toggle user message: verify collapse/expand
- Toggle assistant message: verify all stages hide/show
- Rapid toggling: no UI glitches
- Page reload: collapsed state resets (acceptable, not persisted)

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
