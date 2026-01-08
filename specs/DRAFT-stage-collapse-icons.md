## DRAFT SPECIFICATION: Stage Collapse Icons

### Overview
Add collapse/expand functionality to each stage component (Stage1, Stage2, Stage3, Stage4) via a chevron icon in the stage title. When collapsed, stage content hides but title remains visible.

### User Stories
1. User clicks chevron on Stage 1 -> content collapses, title stays visible
2. User clicks chevron again -> content expands
3. Each stage collapse state is independent
4. Default state: expanded

### Technical Approach

#### 1. Create Shared CollapseIcon Component
**File**: `frontend/src/components/CollapseIcon.jsx` (NEW)

Extract existing CollapseIcon from ChatInterface.jsx:40-50 into reusable component.

#### 2. Add CSS to Stage1.css
Reuse existing `.collapse-toggle`, `.collapse-icon` patterns from ChatInterface.css. Add:
- `.stage-header` - flex container for title + toggle
- `.stage-collapse-toggle` - button styles
- `.stage-content.collapsed` - display:none

#### 3. Modify Each Stage Component
Pattern for all 4 stages:
1. Add `const [isCollapsed, setIsCollapsed] = useState(false)`
2. Wrap `<h3 className="stage-title">` in `<div className="stage-header">` with toggle button
3. Wrap all content after title in `<div className="stage-content">` with conditional collapsed class

### Files to Modify
| File | Change |
|------|--------|
| `CollapseIcon.jsx` | NEW shared component |
| `Stage1.css` | ADD collapse CSS |
| `Stage1.jsx` | ADD collapse state + wrapper divs |
| `Stage2.jsx` | ADD collapse state + wrapper divs |
| `Stage3.jsx` | ADD collapse state + wrapper divs |
| `Stage4.jsx` | ADD collapse state + wrapper divs |
| `ChatInterface.jsx` | OPTIONAL: import shared CollapseIcon |

### Decomposition Justification
| Sub-Task | Traces To Root Term | Because |
|----------|---------------------|---------|
| Create CollapseIcon | "collapse icon" | Icon for toggle |
| Add CSS | "toggles collapse/expand" | Visual state |
| Modify Stage1-4 | "each stage" | Each needs collapse |

### Acceptance Criteria
- [ ] Each stage (1-4) has clickable chevron icon next to title
- [ ] Clicking chevron toggles content visibility
- [ ] Collapsed state shows only title
- [ ] Each stage independent
- [ ] Chevron rotates 90deg when collapsed
- [ ] Hover state on button
