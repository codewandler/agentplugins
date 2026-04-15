---
trigger: design, architecture, design doc
---

# Step 2: Git Worktrees

**Trigger**: After design approval. Creates isolated workspace for the new feature.

**Goal**: Prevent unstable code from interfering with the main codebase. Enable parallel development.

## Process

### 1. Create Feature Branch

```bash
# Check current state
git status
git branch

# Create and switch to new feature branch
git checkout -b feature/{descriptive-name}
```

### 2. Project Setup

```bash
# Verify dependencies are installed
go mod tidy
go mod download

# Verify clean test baseline
go test ./... -count=1
```

### 3. Document the Branch Context

Save to `.agents/plans/BRANCH-{timestamp}.md`:
- Branch name
- Design document reference
- Initial state (tests passing, build passing)
- Planned task list

## When to Use Worktrees

| Situation | Action |
|-----------|--------|
| Single small change | Feature branch is fine |
| Multi-file feature | Feature branch required |
| Breaking changes | Feature branch required |
| Side-by-side work | Git worktree recommended |
| Long-running feature | Git worktree recommended |

## Cleanup

When finished:
```bash
# After merging or discarding
git checkout main
git branch -d feature/{name}
```

## Anti-patterns

| ❌ Don't | ✅ Do |
|----------|-------|
| Work directly on main | Always use feature branches |
| Leave uncommitted changes | Commit or stash before switching |
| Skip the test baseline | Verify tests pass first |
| Forget to document scope | Save branch context |

## Output

After this step, you should have:
- ✅ Feature branch created
- ✅ Project dependencies verified
- ✅ Clean test baseline confirmed
- ✅ Ready to write the plan
