---
executor: bdd
source_feature: ./tests/bdd/chat-url-routing.feature
---

<objective>
Implement Chat URL Routing (Frontend) feature as defined by the BDD scenarios below.
The implementation must make all Gherkin scenarios pass.

URL should reflect the currently selected chat, enabling bookmarking, sharing, and direct navigation.
</objective>

<gherkin>
Feature: Chat URL Routing
  As an authenticated user
  I want the URL to reflect the currently selected chat
  So that I can bookmark, share, and navigate directly to specific conversations

  Background:
    Given I am logged in as a user

  # Happy Paths - URL Navigation

  Scenario: URL updates when selecting a chat from sidebar
    Given I have a conversation in my chat history
    When I select that conversation from the sidebar
    Then the URL should update to include the conversation identifier
    And the selected conversation should display

  Scenario: Navigate directly to a chat via URL
    Given I have an existing conversation
    When I navigate directly to the URL for that conversation
    Then that conversation should load and display
    And the sidebar should highlight that conversation

  Scenario: Create new conversation updates URL
    Given I am on the chat page
    When I create a new conversation
    Then the URL should update to include the new conversation identifier
    And a blank conversation should display

  Scenario: Browser back button navigates chat history
    Given I have selected multiple conversations in sequence
    When I press the browser back button
    Then the previously selected conversation should display
    And the URL should reflect the previous conversation

  Scenario: Browser forward button navigates chat history
    Given I have used the back button to return to a previous conversation
    When I press the browser forward button
    Then the next conversation in history should display
    And the URL should reflect that conversation

  # Edge Cases

  Scenario: Navigate to base chat URL with no conversation selected
    Given I have conversations in my history
    When I navigate to the base chat URL without a conversation identifier
    Then no conversation should be selected
    And the sidebar should display my conversation list

  Scenario: Navigate to URL for non-existent conversation
    Given I am logged in
    When I navigate to a URL with a conversation identifier that does not exist
    Then I should be redirected to the base chat page
    And I should see a message indicating the conversation was not found

  Scenario: Conversation list filtered to current user only
    Given there are conversations belonging to multiple users in the system
    When I view my conversation list
    Then I should only see conversations that belong to me
    And I should not see conversations belonging to other users

  # Authentication and Authorization

  Scenario: Access denied when viewing another user's conversation
    Given another user has a conversation
    When I attempt to navigate to the URL for that conversation
    Then I should be redirected to the base chat page
    And I should see a message indicating access is denied

  Scenario: Unauthenticated user redirected from chat URL
    Given I am not logged in
    When I navigate to a chat URL with a conversation identifier
    Then I should be redirected to the landing page
    And I should be prompted to log in

  Scenario: Unauthenticated user redirected from base chat page
    Given I am not logged in
    When I navigate to the base chat page
    Then I should be redirected to the landing page
</gherkin>

<requirements>
Based on the Gherkin scenarios, implement:

1. **Route Parameter** (Scenarios 1-6)
   - Add `/chat/:conversationId` route to main.jsx
   - Support optional parameter (base `/chat` still works)

2. **URL Sync with Selection** (Scenarios 1, 3)
   - When user selects conversation, update URL via navigate()
   - When creating new conversation, navigate to `/chat/{newId}`

3. **Direct URL Navigation** (Scenario 2)
   - Read conversationId from useParams()
   - Load conversation when URL param changes
   - Highlight active conversation in sidebar

4. **Browser History** (Scenarios 4, 5)
   - Use React Router's navigate() (not window.location)
   - Browser back/forward buttons handled automatically

5. **Base URL Handling** (Scenario 6)
   - `/chat` without param shows no conversation selected
   - Sidebar displays conversation list

6. **Error Handling** (Scenario 7)
   - 404 response redirects to /chat with "not found" message
   - Display toast/alert for error message

7. **Authorization** (Scenarios 8-9)
   - 403 response redirects to /chat with "access denied" message
   - Backend handles ownership validation (frontend handles response)

8. **Auth Guards** (Scenarios 10-11)
   - 401 response redirects to landing page
   - Unauthenticated users cannot access /chat routes

Edge Cases:
- Non-existent conversation ID in URL
- User navigating to another user's conversation
- Unauthenticated access to chat pages
- Browser refresh on conversation URL

</requirements>

<context>
BDD Specification: specs/BDD-SPEC-chat-url-routing.md
Gap Analysis: specs/GAP-ANALYSIS-chat-url-routing-frontend.md

Files to Modify:
- frontend/src/main.jsx - Add route with :conversationId param
- frontend/src/App.jsx - Add useParams, useNavigate, sync URL with state
- frontend/src/components/Sidebar.jsx - Use navigate() for selection
- frontend/src/api.js - Add error.status to thrown errors

Reuse Opportunities:
- BrowserRouter already configured in main.jsx
- Route component pattern exists (LandingPage, Chat)
- useState(currentConversationId) pattern exists
- handleSelectConversation callback exists
- loadConversation async function exists

New Components Needed:
- useParams() hook in App.jsx
- useNavigate() hook in App.jsx and Sidebar.jsx
- Error state for toast messages
- Optional: ProtectedRoute wrapper for auth guards
</context>

<implementation>
Follow TDD approach:
1. Tests will be created from Gherkin scenarios
2. Implement code to make tests pass
3. Ensure all scenarios are green

Architecture Guidelines:
- Use React Router hooks (useParams, useNavigate)
- Sync URL param with component state via useEffect
- Handle API errors with status codes
- Use navigate() for all navigation (enables browser history)
- Keep existing mobile handling logic

Implementation Steps:
1. main.jsx: Add route `<Route path="/chat/:conversationId" element={<App />} />`
2. App.jsx: Import useParams, useNavigate from react-router-dom
3. App.jsx: Get conversationId from useParams()
4. App.jsx: useEffect to sync conversationId param with state
5. App.jsx: Update handleSelectConversation to call navigate()
6. App.jsx: Update handleNewConversation to call navigate() after creation
7. App.jsx: Handle 401/403/404 in loadConversation with appropriate redirects
8. Sidebar.jsx: Import useNavigate, call navigate() on selection
9. api.js: Add error.status to thrown errors for status code handling
</implementation>

<verification>
All Gherkin scenarios must pass:
- [ ] Scenario: URL updates when selecting a chat from sidebar
- [ ] Scenario: Navigate directly to a chat via URL
- [ ] Scenario: Create new conversation updates URL
- [ ] Scenario: Browser back button navigates chat history
- [ ] Scenario: Browser forward button navigates chat history
- [ ] Scenario: Navigate to base chat URL with no conversation selected
- [ ] Scenario: Navigate to URL for non-existent conversation
- [ ] Scenario: Conversation list filtered to current user only
- [ ] Scenario: Access denied when viewing another user's conversation
- [ ] Scenario: Unauthenticated user redirected from chat URL
- [ ] Scenario: Unauthenticated user redirected from base chat page
</verification>

<success_criteria>
- All 11 Gherkin scenarios pass
- URL reflects current conversation selection
- Browser back/forward buttons work correctly
- Error responses (401/403/404) handled with appropriate UI feedback
- Code follows React Router best practices
- Existing functionality (mobile view, streaming, etc.) preserved
</success_criteria>
