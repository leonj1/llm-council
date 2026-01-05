In all interactions be extremely concise and sacrifice grammar for the sake of concision.

### Session Continuity Files

| File | Purpose |
|------|---------|
| `claude-progress.txt` | Session log showing what agents have done across context windows |
| `architects_digest.md` | Recursive task breakdown and architecture state |
| `feature_list.md` | Comprehensive feature requirements with completion status |
| `.feature_list.md.example` | Example template created if `feature_list.md` is missing |


### Hierarchical Traceability (Decomposition Support)

Complex requests get broken into sub-tasks. The validator supports **three validation modes**:

| Mode | When Used | What It Checks |
|------|-----------|----------------|
| **Direct** | Spec or scenario (leaf node) | Root request terms appear in artifact |
| **Decomposition** | Task broken into sub-tasks | Each sub-task traces to root; all root terms covered |
| **Aggregation** | All sub-tasks complete | Sum of sub-tasks fulfills original request |

**Example Valid Decomposition**:
```
Root Request: "Build an org chart landing page"
├── 1. Create employee data model     ← Traces to "org chart"
├── 2. Build tree component           ← Traces to "org chart"
├── 3. Design landing page layout     ← Traces to "landing page"
└── 4. Integrate chart into page      ← Traces to both
```

**Example Invalid Decomposition (DRIFT)**:
```
Root Request: "Build an org chart landing page"
├── 1. Create employee data model     ← OK
├── 2. Build productivity dashboard   ← DRIFT: "dashboard" ≠ "landing page"
├── 3. Add team metrics               ← DRIFT: not in root request
└── 4. Create reporting system        ← DRIFT: not in root request
```

**Decomposition Justification Requirement**:
When the architect decomposes a task, they MUST include a justification table in `architects_digest.md`:

```markdown
## Root Request
"Build an org chart landing page"

### Decomposition Justification for Task 1
| Sub-Task | Traces To Root Term | Because |
|----------|---------------------|---------|
| 1.1 Employee data model | "org chart" | Chart needs employee data |
| 1.2 Tree component | "org chart" | Visual hierarchy display |
| 1.3 Landing layout | "landing page" | Page structure |
| 1.4 Integration | Both | Combines into final product |
```

Without this justification, the validator will REJECT the decomposition.

### Feature List Protocol

The `feature_list.md` file prevents two common agent failure modes:
- **One-shotting**: Trying to implement everything at once
- **Premature victory**: Declaring the project done before all features work

**Rules for agents**:
1. Only modify the status checkbox - Never remove or edit feature descriptions
2. Mark `[x] Complete` only after verified testing - Not after implementation
3. Work on one feature at a time - Incremental progress
4. Read feature list at session start - Choose highest-priority incomplete feature

### CRASH-RCA Scripts

Located in `.claude/scripts/`:

- **crash.py** - State manager for forensic debugging sessions
  - `crash.py start "issue"` - Initialize session
  - `crash.py step --hypothesis "..." --action "..." --confidence 0.7` - Log investigation step
  - `crash.py status` - Check session state
  - `crash.py diagnose --root_cause "..." --justification "..." --evidence "..."` - Complete with RCA
  - `crash.py cancel` - Abort session

## Documentation Guidelines

- Place markdown documentation in `./docs/`
- Keep `README.md` in the root directory
- Ensure all header/footer links have actual pages (no 404s)

## Database Migration Rules (Flyway)

If the project already has a `./sql` folder, you cannot modify any of these existing files since these are used for Flyway migrations. Your only option if you need to make changes to the database schema is to add new `.sql` files.

## Workflow Comparison

### BDD-TDD Workflow (`/architect`)
**Best for**: New features with comprehensive test coverage, behavior-driven development

**Flow**:
1. `init-explorer` gathers project context, creates `architects_digest.md`
2. `architect` creates greenfield spec (or decomposes complex tasks)
3. `request-fidelity-validator` validates spec preserves user's exact request (loops back to architect if drift detected)
4. `bdd-agent` generates Gherkin scenarios
5. `request-fidelity-validator` validates scenarios preserve user's exact request (loops back to bdd-agent if drift detected)
6. `scope-manager` validates complexity (loops back to Architect if too complex)
7. `test-consistency-validator` validates Gherkin scenario names match their steps (loops back to bdd-agent if inconsistent)
8. `gherkin-to-test` invokes codebase-analyst and creates prompts
9. `run-prompt` executes prompts sequentially
10. For each prompt:
    - `test-creator` writes tests from Gherkin
    - `test-consistency-validator` validates test names match content (loops back to test-creator if inconsistent)
    - `test-evaluator` evaluates assertion quality (loops back to test-creator if weak assertions)
    - `coder-orchestrator` reads ONE task and delegates to coder
    - `coder` implements to pass tests
    - `coding-standards-checker` verifies quality (runs after each coder task)
    - `tester` validates functionality (runs after each coder task)
    - `post-coder-orchestrator-loop.py` hook checks for remaining tasks (loops back to coder-orchestrator if tasks remain)
    - `bdd-test-runner` validates test infrastructure (Dockerfile.test, Makefile, `make test`)

**Benefits**:
- Session continuity via `claude-progress.txt` and `feature_list.md`
- Prevents one-shotting and premature victory
- Tests derived from business-readable Gherkin scenarios
- Clear traceability from requirements to tests to code
- Full quality gates
- Living documentation via `.feature` files

### Direct Implementation (`/coder`)
**Best for**: Quick fixes, manual orchestration, iterative development

**Flow**:
1. Orchestrator breaks down task into todos
2. `coder-orchestrator` reads ONE task and delegates to coder
3. `coder` agent implements the single task
4. `coding-standards-checker` verifies code quality (runs after each coder task)
5. `tester` validates functionality (runs after each coder task)
6. `post-coder-orchestrator-loop.py` hook checks for remaining tasks (loops back to step 2 if tasks remain)

**Benefits**:
- Manual control over task breakdown
- Direct implementation without test-first approach
- Iterative todo-based workflow
- Coder receives ONE task at a time (lean context)
- Quality gates run after each task, not batched at end

### Prompt Execution (`run-prompt` agent)
**Best for**: Executing pre-created prompts, batch operations

**Invocation**: `Task(subagent_type="run-prompt", prompt="005 006 007 --sequential")`

**Flow**:
- Detects task type (TDD, BDD, direct code, or research)
- Routes to appropriate workflow
- Can execute multiple prompts in parallel or sequential
- Supports executor override via frontmatter (`tdd`, `bdd`, `coder`, `general-purpose`)

**Benefits**:
- Flexible execution strategies
- Batch processing
- Intelligent routing
- BDD prompts always run sequentially

## Available Skills

## MANDATORY: Skill Discovery Protocol

Before implementing ANY user request, you MUST:
1. invoke the skill discovery API FIRST**
   - Call: `discover_skills(user_request)` 
   - Wait for the response before proceeding
   - Follow the returned skill instructions in dependency order

2. **Never skip skill discovery for:**
   - Creating new projects or applications
   - Setting up infrastructure
   - Deploying services
   - Configuring authentication, databases, or CI/CD

3. **You may skip skill discovery for:**
   - Simple questions or explanations
   - Code review of existing files
   - Debugging existing code
   - General conversation

4. **If an agent or slash command cannot find a skill then ask for that skill by name by:**
   - Call: `discover_skills(user_request)` 
   - Wait for the response before proceeding
   - Follow the returned skill instructions in dependency order

## Why This Matters
Organization skills encode team standards, security requirements, and approved patterns.
Skipping skill discovery means potentially violating compliance requirements.
