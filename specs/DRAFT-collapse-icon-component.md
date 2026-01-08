# DRAFT: Shared CollapseIcon Component + CSS

## Root Request Traceability
**Root**: "Add a collapse icon to each stage (stage 1, stage 2, etc.) that toggles collapse/expand of just the selected stage"

**This Sub-Task**: Create shared CollapseIcon component + CSS

**Traces To**: "collapse icon" - the reusable visual component all stages will use

---

## Overview
Create a reusable CollapseIcon React component with accompanying CSS that renders a chevron icon which visually indicates collapsed/expanded state.

---

## Interfaces Needed

### ICollapseIconProps
```typescript
interface ICollapseIconProps {
  isCollapsed: boolean;       // Current state
  onClick: () => void;        // Toggle callback
  ariaLabel?: string;         // Accessibility label
}
```

### ICollapseIconState
No internal state - fully controlled component.

---

## Data Models

### CSS Classes
```css
.collapse-icon           /* Container for clickable area */
.collapse-icon--collapsed /* Modifier when collapsed */
.collapse-icon--expanded  /* Modifier when expanded */
.collapse-icon__chevron   /* The chevron element itself */
```

---

## Logic Flow

```
CollapseIcon(props):
  1. Destructure { isCollapsed, onClick, ariaLabel }
  2. Determine rotation class based on isCollapsed
     - collapsed: chevron points right (0deg)
     - expanded: chevron points down (90deg)
  3. Render button with:
     - onClick handler
     - aria-label for accessibility
     - aria-expanded attribute
     - Chevron SVG or unicode character
  4. Return JSX
```

---

## File Structure

| File | Purpose |
|------|---------|
| `frontend/src/components/CollapseIcon.jsx` | React component |
| `frontend/src/components/CollapseIcon.css` | Styling |

---

## Component Implementation (Pseudocode)

```jsx
// CollapseIcon.jsx
import './CollapseIcon.css';

function CollapseIcon({ isCollapsed, onClick, ariaLabel = "Toggle collapse" }) {
  const stateClass = isCollapsed ? 'collapse-icon--collapsed' : 'collapse-icon--expanded';

  return (
    <button
      className={`collapse-icon ${stateClass}`}
      onClick={onClick}
      aria-label={ariaLabel}
      aria-expanded={!isCollapsed}
      type="button"
    >
      <span className="collapse-icon__chevron">&#9654;</span>
    </button>
  );
}

export default CollapseIcon;
```

---

## CSS Implementation (Pseudocode)

```css
/* CollapseIcon.css */
.collapse-icon {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px 8px;
  display: inline-flex;
  align-items: center;
  transition: transform 0.2s ease;
}

.collapse-icon:hover {
  opacity: 0.7;
}

.collapse-icon__chevron {
  display: inline-block;
  transition: transform 0.2s ease;
}

.collapse-icon--collapsed .collapse-icon__chevron {
  transform: rotate(0deg);
}

.collapse-icon--expanded .collapse-icon__chevron {
  transform: rotate(90deg);
}
```

---

## Context Budget

| Metric | Estimate |
|--------|----------|
| Files to read | 0 (greenfield component) |
| New code to write | ~40 lines (JSX + CSS) |
| Test code to write | ~30 lines |
| **Estimated context usage** | **5%** |

---

## Acceptance Criteria

1. CollapseIcon renders a clickable chevron
2. Chevron rotates 90deg when isCollapsed changes
3. onClick callback fires when clicked
4. Accessible via keyboard (button element)
5. aria-expanded reflects current state
