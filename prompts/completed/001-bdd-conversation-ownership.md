---
executor: bdd
source_feature: ./tests/bdd/conversation-ownership.feature
---

<objective>
Implement the Conversation Ownership feature as defined by the BDD scenarios below.
The implementation must make all Gherkin scenarios pass.
Users must only access their own conversations - ownership is enforced on all conversation endpoints.
</objective>

<gherkin>
Feature: Conversation Ownership
  As an authenticated user
  I want my conversations to be private to my account
  So that other users cannot access my chat history

  Background:
    Given I am logged in as a user

  # Ownership Assignment

  Scenario: New conversation is assigned to creating user
    Given I am logged in
    When I create a new conversation
    Then that conversation should be associated with my user account

  # Ownership Validation on Retrieval

  Scenario: Successfully retrieve my own conversation
    Given I have created a conversation
    When I request that conversation
    Then I should receive the conversation details
    And the response should include all messages in that conversation

  Scenario: Cannot retrieve conversation owned by another user
    Given another user has created a conversation
    When I request that conversation
    Then I should receive an access denied response
    And no conversation data should be returned

  Scenario: Cannot list conversations owned by other users
    Given multiple users have created conversations
    When I request my conversation list
    Then I should only see conversations I created
    And the count should match my conversation count

  # Error Cases

  Scenario: Request non-existent conversation returns not found
    Given I am logged in
    When I request a conversation that does not exist
    Then I should receive a not found response

  Scenario: Request conversation without authentication returns unauthorized
    Given I have a conversation
    When I request that conversation without being logged in
    Then I should receive an unauthorized response
</gherkin>

<requirements>
Based on the Gherkin scenarios, implement:

1. **Auth Dependency** - Create `require_auth` FastAPI dependency in `backend/auth.py`
   - Extract session_id from cookie
   - Return user dict from sessions store
   - Raise 401 HTTPException if missing/invalid session

2. **Storage Layer Changes** - Modify `backend/storage.py`
   - Add `user_id` parameter to `create_conversation()`
   - Store `user_id` in conversation JSON
   - Add `user_id` filter to `list_conversations()`
   - Return only conversations matching the user_id

3. **Endpoint Ownership Validation** - Modify `backend/main.py`
   - Inject `require_auth` dependency on all conversation endpoints
   - POST /api/conversations: Pass user_id to storage
   - GET /api/conversations: Filter by user_id
   - GET /api/conversations/{id}: Check ownership, return 403 if mismatch
   - DELETE /api/conversations/{id}: Check ownership before delete
   - POST /api/conversations/{id}/message: Check ownership before adding message

Edge Cases to Handle:
- Missing session cookie -> 401 Unauthorized
- Invalid/expired session -> 401 Unauthorized
- Non-existent conversation -> 404 Not Found
- Conversation owned by different user -> 403 Access Denied
- Empty conversation list for new user -> Return empty array

</requirements>

<context>
BDD Specification: specs/BDD-SPEC-conversation-ownership.md
Gap Analysis: specs/GAP-ANALYSIS.md

Reuse Opportunities (from gap analysis):
- `backend/auth.py` has `sessions` dict and `get_current_user()` pattern
- `backend/database.py` has `get_chat_by_id()` returning `user_id` (ownership pattern)
- `backend/database.py` has `get_chats_by_user_id()` (filter pattern)
- Session user dict contains `user_id` from database

New Components Needed:
- `require_auth` dependency function in auth.py
- `user_id` field in conversation storage
- Ownership check helper function

Files to Modify:
| File | Changes |
|------|---------|
| `backend/auth.py` | Add `require_auth` dependency |
| `backend/storage.py` | Add user_id to create/list functions |
| `backend/main.py` | Add auth dependency, ownership checks |
</context>

<implementation>
Follow TDD approach:
1. Tests will be created from Gherkin scenarios
2. Implement code to make tests pass
3. Ensure all scenarios are green

Architecture Guidelines:
- Follow strict-architecture rules (500 lines max, interfaces, no env vars in functions)
- Use existing patterns from codebase (session cookie, HTTPException)
- Maintain consistency with existing auth.py structure
- Keep ownership check logic simple and testable

Implementation Pattern:
```python
# In auth.py
async def require_auth(request: Request) -> dict:
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return sessions[session_id]

# In main.py endpoints
@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, user: dict = Depends(require_auth)):
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conversation.get("user_id") != user.get("user_id"):
        raise HTTPException(status_code=403, detail="Access denied")
    return conversation
```
</implementation>

<verification>
All Gherkin scenarios must pass:
- [ ] Scenario: New conversation is assigned to creating user
- [ ] Scenario: Successfully retrieve my own conversation
- [ ] Scenario: Cannot retrieve conversation owned by another user
- [ ] Scenario: Cannot list conversations owned by other users
- [ ] Scenario: Request non-existent conversation returns not found
- [ ] Scenario: Request conversation without authentication returns unauthorized
</verification>

<success_criteria>
- All 6 Gherkin scenarios pass
- Code follows project coding standards
- Tests provide complete coverage of scenarios
- Implementation matches user's confirmed intent
- No regression in existing functionality
- Proper HTTP status codes (401, 403, 404)
</success_criteria>
