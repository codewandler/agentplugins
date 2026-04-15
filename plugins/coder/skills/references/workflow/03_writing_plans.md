---
trigger: make a plan, write a plan, plan to, break down, task list
---

# Step 3: Writing Plans

**Trigger**: After design approval. Breaks the design into bite-sized tasks.

**Goal**: Create a task list so detailed that a "junior engineer with poor taste, no judgement, no project context, and an aversion to testing" could follow it.

## Process

### 1. Review the Design Document

Read `.agents/plans/DESIGN-{timestamp}.md` and ensure you understand:
- Scope and acceptance criteria
- Key design decisions
- Out-of-scope items

### 2. Break Down Into Tasks

Each task MUST include:
- **Task ID**: `Task 1`, `Task 2`, etc.
- **Title**: One-line description
- **Files to modify**: Exact paths (e.g., `pkg/foo/bar.go`)
- **Files to create**: Exact paths with initial structure
- **Code to write**: Complete code snippets, not pseudocode
- **Verification**: Specific commands to run to confirm success
- **Time estimate**: 2-5 minutes per task

### 3. Order Dependencies

Tasks must be ordered such that each task can be completed independently after the previous one finishes.

```
Task 1: Scaffold project structure
  → Creates directories, initial files
Task 2: Define data types
  → Depends on: Task 1
Task 3: Implement core logic
  → Depends on: Task 2
```

### 4. Apply YAGNI and DRY

**YAGNI** — You Aren't Gonna Need It
- Only include what's explicitly in the design
- If you don't know if something is needed, ask

**DRY** — Don't Repeat Yourself
- Extract common patterns into shared functions
- Reuse existing utilities

## Task Template

```
### Task N: {Title}

**Files modified**: path/to/file.go
**Files created**: path/to/new.go
**Estimated time**: 3 minutes

**Code to write**:

// path/to/new.go
package foo

// TODO: specific implementation

**Verification**:
go build ./path/to/...
go test ./path/to/... -run TestNewFeature
```

## Anti-patterns

| Don't | Do |
|-------|-----|
| Vague tasks like "implement X" | Include exact file paths and code |
| Tasks over 10 minutes | Split into smaller tasks |
| Skip verification steps | Always include build/test commands |
| Include features not in design | Ask if unclear, don't assume |

## Output

Save to `.agents/plans/PLAN-{timestamp}.md`:
- Reference to design document
- Ordered list of tasks with verification steps
- Total estimated time

## When Done

Show the plan to the user and ask: "Ready to execute?"
