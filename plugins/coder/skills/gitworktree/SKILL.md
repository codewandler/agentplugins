---
name: git-worktree
description: Use git worktrees to work on multiple branches simultaneously without checking out
trigger: git worktree
---

# Git Worktree Skill

Use `git worktree` to create multiple working directories from a single repository.
Each worktree is attached to a different branch, allowing parallel development without
`git checkout` overhead.

---

## When to Use

- **Parallel work**: Switch between branches without stashing or committing work-in-progress
- **Code review**: Check out a PR branch while continuing work on main
- **Long-running builds**: Keep a branch checked out while running tests on another
- **Bisect sessions**: Isolate a bisect investigation in its own worktree

---

## Convention: Use `.work/` Folder

All worktrees should be created inside a `.work/` folder in the repository root.
This keeps worktrees organized and isolated from the main codebase.

**`.work/` is gitignored** — worktrees are not committed.

---

## Essential Commands

### List all worktrees

```bash
git worktree list
```

Output shows each worktree path, the branch it is on, and whether it is locked or bare:

```
/path/to/main        abc1234 [main]
/path/to/feature-a   def5678 [feature-a]
/path/to/bugfix      (detached)
```

### Create a worktree with a new branch

```bash
git worktree add <path> -b <branch-name>
```

**Example**: Create `.work/feature-x` based on `main`, checked out as `feature-x`:

```bash
git worktree add .work/feature-x -b feature-x
```

### Create a worktree from an existing branch

```bash
git worktree add <path> <branch>
```

**Example**: Check out the existing `develop` branch in a new directory:

```bash
git worktree add .work/develop develop
```

### Create a worktree from a remote branch

```bash
git worktree add <path> -b <new-branch> <remote>/<branch>
```

**Example**: Track `origin/feature-y` as a new local branch:

```bash
git worktree add .work/feature-y -b feature-y origin/feature-y
```

### Remove a worktree

```bash
git worktree remove <path>
```

Use `--force` if the worktree has untracked or uncommitted changes you want to discard:

```bash
git worktree remove <path> --force
```

### Prune stale worktree references

Worktree entries become stale when a directory is manually deleted. Clean them up with:

```bash
git worktree prune
```

---

## Common Patterns

### Working on a PR while keeping main checked out

```bash
# Create a worktree for the PR
git worktree add .work/pr-123 -b pr-123 origin/pr/123

# Work in .work/pr-123 as usual (commit, push, etc.)
# Meanwhile, main remains checked out in the original directory
```

### Keep work-in-progress off the current branch

```bash
# Suspend current work without committing
git stash

# Create a worktree for experimental changes
git worktree add .work/experiment -b experiment

# Resume main work in the original directory
# When ready, return to the experiment worktree and continue
```

### Using with `git fetch --all` for stale remotes

If a remote branch was deleted but worktree references persist, fetch updates first:

```bash
git fetch --all --prune
git worktree prune
```

---

## Limitations and Gotchas

- **Shared `.git`**: All worktrees share the same repository database.
  A `git gc` or `git push` in one worktree affects all of them.
- **Branch name uniqueness**: A branch cannot be checked out in multiple worktrees simultaneously.
- **Bare worktrees**: A worktree created with `git worktree add <path>` (no branch argument)
  enters a detached HEAD state — no branch is associated.
- **Locking**: Lock a worktree to prevent accidental modification or removal:

  ```bash
  git worktree lock <path> [-m|--reason <text>]
  ```

  Unlock with:

  ```bash
  git worktree unlock <path>
  ```

- **Moving worktrees**: Use `git worktree move <old-path> <new-path>`.
  Do not manually `mv` directories — this leaves stale references.

---

## Quick Reference

| Goal                          | Command                                                      |
|-------------------------------|--------------------------------------------------------------|
| List all worktrees            | `git worktree list`                                          |
| Create + new branch           | `git worktree add <path> -b <branch>`                        |
| Create from existing branch   | `git worktree add <path> <branch>`                           |
| Create from remote branch     | `git worktree add <path> -b <branch> <remote>/<branch>`      |
| Remove a worktree             | `git worktree remove <path>`                                 |
| Remove with uncommitted work  | `git worktree remove <path> --force`                         |
| Prune stale references        | `git worktree prune`                                         |
| Lock a worktree               | `git worktree lock <path>`                                   |
| Unlock a worktree             | `git worktree unlock <path>`                                 |
| Move a worktree               | `git worktree move <old-path> <new-path>`                    |
