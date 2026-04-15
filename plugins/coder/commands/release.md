---
description: Create a release—tag, update CHANGELOG, and push GitHub release
aliases: [rel]
---

# Release Workflow

Follow these steps to release the current project version, including git tagging,
CHANGELOG publication, and GitHub release creation (if applicable).

## Step 1: Validate Repository is Clean

Run `git status` to confirm there are no uncommitted changes or untracked files.
If the repository has pending changes, tell the user and stop. Releases must be
made from a clean working tree.

## Step 2: Verify Remote and Authentication

Check that the repository has a `origin` remote pointing to GitHub (or another remote).
Run `git remote -v` to display remotes.

If this is a GitHub repository, verify that GitHub CLI (`gh`) is available and authenticated:
```
which gh
gh auth status
```

If GitHub CLI is not available or not authenticated, note this and proceed without
automatic release creation (skip Step 8).

## Step 3: Find the Last Published Tag

Run these commands to find the most recent semantic version tag:

```
git describe --tags --abbrev=0
```

If no tags exist, the first release will be `v0.1.0`. Otherwise, parse the last tag's
version number.

## Step 4: Review and Validate CHANGELOG.md

Read `CHANGELOG.md` and examine the `[Unreleased]` section:

- Is there an `[Unreleased]` section?
- Does it have `Added`, `Changed`, `Fixed`, `Removed` subsections?
- Is each subsection populated with meaningful entries (not empty bullet lists)?

**If the [Unreleased] section is missing or incomplete:**

- Run `git log <last-tag>..HEAD --oneline` to see all commits since the last release
- Extract meaningful high-level changes from the commits
- Add missing entries to the `[Unreleased]` section under the correct subsection
- Group similar changes (e.g., all "Added" items under "Added")

**If entries are vague (e.g. "fixed bugs"), ask the user for clarification:**
- "The CHANGELOG has vague entries. Can you clarify what this feature does?"
- Wait for user input before proceeding.

## Step 5: Infer the Next Semantic Version

Analyze the `[Unreleased]` section to determine the next version:

- **Major (X.0.0)**: If `BREAKING CHANGE:` appears in any entry
- **Minor (x.Y.0)**: If `Added` subsection has entries (new features)
- **Patch (x.y.Z)**: If only `Changed`, `Fixed`, or `Removed` (no new features)

Default to **Patch** if `[Unreleased]` is empty.

**Example reasoning:**
- Last tag: `v1.2.3`
- `[Unreleased]` has entries in `Added` and `Fixed` → next version is `v1.3.0`
- `[Unreleased]` has only `Fixed` → next version is `v1.2.4`
- `[Unreleased]` has `BREAKING CHANGE:` → next version is `v2.0.0`

## Step 6: Update CHANGELOG.md with the New Version

Rename the `[Unreleased]` section header to `[vX.Y.Z] — YYYY-MM-DD`:

**Before:**
```markdown
## [Unreleased]

### Added
- Feature A
```

**After:**
```markdown
## [Unreleased]

---

## [v1.3.0] — 2026-04-11

### Added
- Feature A
```

Then add a new empty `[Unreleased]` section at the top:

```markdown
## [Unreleased]

---

## [v1.3.0] — 2026-04-11
...
```

## Step 7: Commit, Tag, and Push

Stage the updated CHANGELOG:

```
git add CHANGELOG.md
git commit -m "chore(release): v<version>"
```

Create an annotated git tag:

```
git tag -a v<version> -m "Release v<version>"
```

Push the release commit and tag to origin:

```
git push origin <current-branch>
git push origin v<version>
```

Show the user what was pushed before continuing.

## Step 8: Create GitHub Release (if applicable)

If this is a GitHub repository and `gh` is available:

1. Extract the release notes from the CHANGELOG for this version only
   (not the entire file—just the version section)

2. Create a GitHub release using `gh` (the tag is already on the remote):

```
gh release create v<version> --title "v<version>" --notes "..."
```

If the release creation fails, note the error but do not stop the workflow—
the tag is already pushed.

## Step 9: Confirm and Show Results

Run these commands to show the results:

```
git log -1 --format=fuller
git tag -l | tail -5
```

If GitHub release was created, show:

```
gh release view v<version>
```

## Rules

- **Pushing is part of Step 7** — the release workflow pushes the commit and tag automatically before creating the GitHub release
- **NEVER create a release with an empty [Unreleased] section** (ask user to commit changes first)
- **If version inference is ambiguous, ask the user** (don't guess)
- **If GitHub CLI is unavailable, skip Step 8 silently** (tag is still created)
- **Always show the tag and release notes before declaring done**
