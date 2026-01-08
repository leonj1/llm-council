# BDD Specification: Stage Collapse Icons

## Overview
Add collapse/expand functionality to each stage component (Stage 1, Stage 2, Stage 3, Stage 4) via a chevron icon in the stage title. When collapsed, stage content hides but the title remains visible. Each stage operates independently.

## User Stories
- As a user of the LLM Council interface, I want to collapse and expand individual stages so that I can focus on the content I care about without scrolling through everything

## Feature Files
| Feature File | Scenarios | Coverage |
|--------------|-----------|----------|
| stage-collapse-icons.feature | 18 | Happy path, independence, defaults, visual feedback, accessibility |

## Scenarios Summary

### stage-collapse-icons.feature

**Happy Path (8 scenarios)**
1. User collapses Stage 1 by clicking the collapse icon
2. User expands a collapsed Stage 1 by clicking the collapse icon
3. User collapses Stage 2 by clicking the collapse icon
4. User expands a collapsed Stage 2 by clicking the collapse icon
5. User collapses Stage 3 by clicking the collapse icon
6. User expands a collapsed Stage 3 by clicking the collapse icon
7. User collapses Stage 4 by clicking the collapse icon
8. User expands a collapsed Stage 4 by clicking the collapse icon

**Independence (2 scenarios)**
9. Collapsing one stage does not affect other stages
10. Multiple stages can be collapsed independently

**Default State (1 scenario)**
11. Stages are expanded by default when conversation loads

**Visual Feedback (3 scenarios)**
12. Collapse icon shows hover state when user hovers over it
13. Collapse icon rotates when stage is collapsed
14. Collapse icon rotates back when stage is expanded

**Accessibility (2 scenarios)**
15. Collapse icon is keyboard accessible
16. Collapse icon has accessible label

## Acceptance Criteria
- Each stage (1-4) has clickable chevron icon next to title
- Clicking chevron toggles content visibility
- Collapsed state shows only title
- Each stage collapse state is independent
- Chevron rotates 90 degrees when collapsed
- Hover state on button
- Default state is expanded
- Keyboard accessible with Enter key
- Screen reader announces collapsed/expanded state
