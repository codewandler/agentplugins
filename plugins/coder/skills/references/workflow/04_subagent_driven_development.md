---
trigger: implement, build, develop, start coding, start implementing
---

# Step 4: Subagent-Driven Development

**Trigger**: After implementation plan is approved. Executes tasks with isolated subagents.

**Goal**: Each task is handled in a clean, isolated context to prevent context pollution and ensure focused execution.

## Two Execution Modes

### Mode A: Subagent-Driven (Recommended for large tasks)

A fresh subagent handles each task independently:
1. Reads the task specification
2. Writes the failing test (TDD)
3. Writes the implementation
4. Runs verification
5. Commits (only if user explicitly instructed)

### Mode B: Batch Execution with Checkpoints

Execute multiple tasks, then pause for human review:
- Good for: learning the codebase, uncertain tasks
- Checkpoint frequency: Every 3-5 tasks or after critical changes

## Task Execution Protocol

For each task in the plan:

### 1. Read Task Specification
```
Task N: {title}
Files: {paths}
Code: {snippets}
Verification: {commands}
```

### 2. Execute with TDD
```
RED  → Write failing test
GREEN → Write minimal implementation
REFACTOR → Clean up
```

### 3. Self-Review Checklist
Before marking complete, verify:
- [ ] Test covers the spec requirements
- [ ] Implementation matches test expectations
- [ ] Code follows project conventions
- [ ] No debug prints or TODOs left
- [ ] Build passes
- [ ] Tests pass

### 4. Report Progress
After each task:
```
✅ Task N complete: {title}
   - Tests passing
   - Build passing
   - Ready for next task
```

## When Stuck

If a task fails after 3 attempts:
1. Document the issue
2. Ask for guidance
3. Do NOT skip the task

## Anti-patterns

| Don't | Do |
|-------|-----|
| Skip verification | Always run tests |
| Move to next task with failing tests | Fix before proceeding |
| Assume context from previous task | Re-read relevant files |
| Rush through TDD | Respect the RED-GREEN-REFACTOR cycle |

## Output

After each task:
- ✅ Tests passing
- ✅ Build passing
- ✅ Changes committed (if instructed)
