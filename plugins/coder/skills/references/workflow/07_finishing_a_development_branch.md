---
trigger: merge, finish, complete, done, wrap up, close the branch
---

# Step 7: Finishing a Development Branch

**Trigger**: When all tasks are complete.

**Goal**: Verify everything works, clean up, and present options for the completed work.

## Pre-Flight Checklist

### Build Verification
```bash
go build ./...
```

### Test Verification
```bash
go test ./... -count=1
```

### Coverage Check
```bash
go test -cover ./...
```

### Lint Check
```bash
golangci-lint run
# or
go vet ./...
```

### No Leftovers
```bash
# Check for debug prints
grep -r "fmt.Print" --include="*.go" .
grep -r "log.Print" --include="*.go" .

# Check for TODO comments left in code
grep -r "TODO" --include="*.go" .

# Check for commented-out code
grep -r "//.*old.*code" --include="*.go" .
```

## Document the Changes

Create a summary of what was done:

```
## Completed: {Feature Name}

### Tasks Completed
- Task 1: {title} ✅
- Task 2: {title} ✅
...

### Tests Added
- TestFeature_Behavior1
- TestFeature_Behavior2
...

### Files Changed
- Added: new.go
- Modified: existing.go
- Deleted: removed.go

### Verification
- Build: ✅ Passing
- Tests: ✅ 42 tests passing
- Coverage: 📊 85%
```

## Cleanup Tasks

### 1. Git Worktree Cleanup
```bash
# If using git worktrees
git worktree list
git worktree remove feature/{name}
```

### 2. Branch Decision

Present options to the user:

```
## Branch Status: feature/{name}

All tasks complete. Tests passing.

Options:
1. **Merge** — Fast-forward merge to main
2. **Pull Request** — Create PR for review
3. **Keep** — Leave branch for later work
4. **Discard** — Delete branch without merging

What would you like to do?
```

### 3. If Merging
```bash
git checkout main
git merge --ff-only feature/{name}
git branch -d feature/{name}
```

### 4. If Creating PR
```bash
git push -u origin feature/{name}
gh pr create --title "feat: {description}" --body "..."
```

## Anti-patterns

| Don't | Do |
|-------|-----|
| Skip the final test run | Always verify before presenting |
| Leave debug code | Clean up before finishing |
| Push without asking | Get user confirmation |
| Skip the summary | Document what was done |
| Rush to finish | Ensure quality first |

## When NOT to Finish

If any of these are true, DO NOT finish:
- Tests are failing
- Build doesn't pass
- Known bugs exist
- User hasn't reviewed the work

Address issues first, then finish.
