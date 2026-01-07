# BDD Specification: Toggle Collapse/Expand Chat Messages

## Overview
Add an icon on each chat message that allows the user to toggle collapsing and expanding the message. This addresses the problem of lengthy messages forcing excessive scrolling.

## User Stories
- As a user viewing lengthy chat messages, I want an icon on each message that allows me to toggle collapsing and expanding, so that I can reduce scrolling and see an overview of the conversation

## Feature Files
| Feature File | Scenarios | Coverage |
|--------------|-----------|----------|
| toggle-collapse-messages.feature | 17 | Happy paths, edge cases, state behavior, loading, visual feedback |

## Scenarios Summary

### toggle-collapse-messages.feature

**Happy Paths (5 scenarios)**
1. User collapses an expanded user message
2. User expands a collapsed user message
3. User collapses an expanded assistant message
4. User expands a collapsed assistant message
5. Messages start in expanded state by default

**Edge Cases (6 scenarios)**
6. Toggle icon visibility on all messages
7. Collapsed preview shows truncated content for user messages
8. Collapsed preview shows placeholder for assistant messages
9. Multiple messages can be collapsed independently
10. Rapid toggling does not cause display issues
11. Short messages still show collapse toggle

**State Behavior (3 scenarios)**
12. Collapsed state is preserved while navigating within conversation
13. Collapsed state resets on page reload
14. New messages appear expanded regardless of other collapsed messages

**Loading States (1 scenario)**
15. Collapse toggle is disabled during message loading

**Visual Feedback (2 scenarios)**
16. Collapse icon rotates to indicate state
17. Collapsed preview has distinct visual styling

## Acceptance Criteria

### Core Functionality
- Each chat message displays a collapse/expand toggle icon
- Clicking the icon toggles the message between collapsed and expanded states
- User messages show truncated preview when collapsed
- Assistant messages hide all stages when collapsed

### State Management
- Messages default to expanded state
- Collapsed state is per-message (independent)
- State persists during conversation navigation
- State resets on page reload (not persisted)

### Visual Design
- Icon rotates to indicate current state (down = expanded, right = collapsed)
- Collapsed preview has distinct styling (muted, italicized)
- Toggle icon positioned consistently on all messages

### Edge Cases Handled
- Short messages still show toggle
- Rapid clicking handled gracefully
- Loading messages have disabled or hidden toggle
- New messages always appear expanded

## Technical Notes

Files to modify:
- `/root/repo/frontend/src/components/ChatInterface.jsx`
- `/root/repo/frontend/src/components/ChatInterface.css`

Key implementation details from spec:
- React useState for collapsed message state (keyed by message index)
- Inline SVG chevron icon (no external dependencies)
- Truncated preview ~100 chars for user messages
- Placeholder text for collapsed assistant messages
