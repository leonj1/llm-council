---
executor: bdd
source_feature: ./tests/bdd/landing-page.feature
---

<objective>
Implement the Landing Page with Hello World feature as defined by the BDD scenarios below.
Add client-side routing to display a landing page with "Hello World" at the root URL ("/") while preserving the existing chat interface at a dedicated route ("/chat").
The implementation must make all Gherkin scenarios pass.
</objective>

<gherkin>
Feature: Landing Page with Hello World
  As a visitor
  I want to see a landing page when I visit the root URL
  So that I have a welcoming entry point to the application

  Background:
    Given the application is running

  # Happy Paths

  Scenario: Visitor sees Hello World on the landing page
    When the visitor navigates to the root URL
    Then the visitor sees the landing page
    And the landing page displays "Hello World"

  Scenario: Visitor can access the chat page from a different route
    When the visitor navigates to the chat route
    Then the visitor sees the chat interface
    And the chat interface is fully functional

  # Navigation

  Scenario: Landing page is the default page at root URL
    When the visitor opens the application
    Then the browser URL is the root path
    And the landing page is displayed

  Scenario: Chat page is accessible at its dedicated route
    When the visitor navigates directly to the chat route
    Then the browser URL shows the chat path
    And the existing chat functionality is available

  # Preservation of Existing Functionality

  Scenario: Existing chat interface remains intact
    When the visitor accesses the chat page
    Then the sidebar is visible
    And the conversation list is available
    And new conversations can be created

  Scenario: Existing conversation functionality works on chat page
    Given the visitor is on the chat page
    When the visitor creates a new conversation
    Then the conversation appears in the sidebar
    And the visitor can send messages
</gherkin>

<requirements>
Based on the Gherkin scenarios, implement:

1. Install react-router-dom dependency for client-side routing
2. Create LandingPage component that displays "Hello World" text
3. Configure BrowserRouter in main.jsx with route definitions
4. Route "/" renders LandingPage component
5. Route "/chat" renders existing App.jsx (chat interface)
6. Preserve ALL existing chat functionality - no code deletion
7. Sidebar visible and functional on /chat route
8. Conversation creation and messaging work on /chat route

Edge Cases to Handle:
- Unknown routes (404 handling optional)
- Direct navigation to /chat URL
- Browser back/forward navigation

Constraints:
- DO NOT delete any existing code
- DO NOT modify Sidebar, ChatInterface, or Stage components
- Minimize changes to App.jsx (wrap or rename only)
</requirements>

<context>
BDD Specification: specs/BDD-SPEC-landing-page-hello-world.md
Gap Analysis: specs/GAP-ANALYSIS.md

Reuse Opportunities (from gap analysis):
- App.jsx: Wrap as chat route, no internal changes
- All existing components: Reuse as-is
- Styling: Existing index.css and App.css patterns

New Components Needed:
- LandingPage.jsx: Simple component with "Hello World"
- Router configuration in main.jsx

Current Stack:
- React 19.2.0
- Vite 7.2.4
- No routing library installed
</context>

<implementation>
Follow TDD approach:
1. Tests will be created from Gherkin scenarios
2. Implement code to make tests pass
3. Ensure all scenarios are green

Implementation Steps:
1. Add react-router-dom to package.json
2. Create frontend/src/pages/LandingPage.jsx
3. Update frontend/src/main.jsx with BrowserRouter and Routes
4. Configure routes: "/" -> LandingPage, "/chat" -> App

Architecture Guidelines:
- Follow strict-architecture rules (500 lines max, interfaces, no env vars in functions)
- Use existing patterns from codebase
- Maintain consistency with project structure
- Keep LandingPage simple and focused
</implementation>

<verification>
All Gherkin scenarios must pass:
- [ ] Scenario: Visitor sees Hello World on the landing page
- [ ] Scenario: Visitor can access the chat page from a different route
- [ ] Scenario: Landing page is the default page at root URL
- [ ] Scenario: Chat page is accessible at its dedicated route
- [ ] Scenario: Existing chat interface remains intact
- [ ] Scenario: Existing conversation functionality works on chat page
</verification>

<success_criteria>
- All Gherkin scenarios pass
- Root URL "/" displays landing page with "Hello World" label
- Chat page accessible at "/chat" route
- All existing chat functionality preserved (sidebar, conversations, messaging)
- No existing code deleted
- Code follows project coding standards
- Tests provide complete coverage of scenarios
</success_criteria>
