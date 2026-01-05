# DRAFT: Landing Page with Hello World

## Root Request
"Create a landing page with a 'Hello World' label that displays when the browser routes to '/' instead of the chat page. Keep the existing chat page accessible at a different route. Do not delete any existing code."

## Overview
Add client-side routing to the React frontend to:
1. Display a new landing page with "Hello World" at `/`
2. Move existing chat functionality to `/chat`
3. Preserve all existing code and functionality

## Technical Approach

### Dependencies Required
- `react-router-dom` - Standard React routing library

### New Components

#### 1. LandingPage Component
**File**: `/root/repo/frontend/src/components/LandingPage.jsx`

```jsx
function LandingPage() {
  return (
    <div className="landing-page">
      <h1>Hello World</h1>
    </div>
  );
}
```

#### 2. LandingPage Styles (Optional)
**File**: `/root/repo/frontend/src/components/LandingPage.css`

Basic centered styling for the Hello World label.

### Modified Files

#### 1. main.jsx
Wrap `App` with `BrowserRouter`:

```jsx
import { BrowserRouter } from 'react-router-dom';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
)
```

#### 2. App.jsx
Add `Routes` and `Route` to define paths:

```jsx
import { Routes, Route } from 'react-router-dom';
import LandingPage from './components/LandingPage';

// Inside App component return:
<Routes>
  <Route path="/" element={<LandingPage />} />
  <Route path="/chat" element={
    <div className={`app ${isMobile ? 'mobile' : ''}`}>
      {/* existing Sidebar and ChatInterface */}
    </div>
  } />
</Routes>
```

## Implementation Steps

1. Install react-router-dom: `npm install react-router-dom`
2. Create LandingPage.jsx component
3. Create LandingPage.css styles
4. Modify main.jsx to add BrowserRouter
5. Modify App.jsx to add Routes

## Verification

1. Navigate to `/` - should show "Hello World"
2. Navigate to `/chat` - should show existing chat interface
3. All existing chat functionality preserved

## Traceability

| Requirement | Implementation |
|-------------|----------------|
| "landing page" | LandingPage.jsx at `/` |
| "Hello World label" | `<h1>Hello World</h1>` in LandingPage |
| "routes to /" | Route path="/" in App.jsx |
| "chat page accessible at different route" | Route path="/chat" |
| "Do not delete existing code" | Existing App.jsx code moved into /chat route |

## Context Budget
Estimated: ~15% (simple routing addition, minimal new code)
