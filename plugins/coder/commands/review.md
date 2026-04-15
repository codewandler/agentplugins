---
description: Review current uncommitted changes in the repository
aliases: [rv]
---

# Code Review Workflow

Review the current uncommitted changes in this repository. Focus on understanding
**why** the changes were made (infer motivation from context) and whether they
achieve that goal correctly.

{{if .Query}}
## Additional Focus

The user has asked you to pay particular attention to:

> {{.Query}}

Apply this as the primary lens for your review.
Cover other areas as usual but address this focus explicitly in your output.
{{end}}

## Step 1: Assess the Current Changes

Run these commands to understand the scope of what changed:

```
git status
git diff --stat
```

If there are no uncommitted changes, tell the user and stop.

If there are staged changes, also run `git diff --cached --stat` to see the full picture.

## Step 2: Detect the Project Language

Determine the primary language of this repository:

- Look for `go.mod` → **Go project**
- Look for `package.json` → **JavaScript/TypeScript project**
- Look for `Cargo.toml` → **Rust project**
- Look for `pyproject.toml` or `requirements.txt` → **Python project**

**If this is a Go project**: load the `golang-pro` skill to bring in Go-specific
expertise. Use `skill_load` with skill name `golang-pro`. If the skill is not
available (not installed), note this and continue — do not block the review.

## Step 3: Understand the Motivation

Before judging the code, **understand why it was written**. Build context from
multiple sources:

### 3a. Read the Full Diff

Run `git diff` (and `git diff --cached` if there are staged changes) to read
every changed line. Do not skim — read thoroughly.

### 3b. Look at Recent Commits

Run `git log --oneline -10` to understand what work preceded these changes.
Look for patterns: is this a continuation of recent work? A bugfix? A new feature?

### 3c. Search for a Related Plan

Check if there is an active plan that describes the intended work:

```
ls -la .agents/plans/ 2>/dev/null
```

If a `.agents/plans/` directory exists, read the most recent `PLAN-*.md` and
`DESIGN-*.md` files. These describe the intended scope and acceptance criteria.

Cross-reference the current changes against the plan:
- Are the changes aligned with the plan?
- Are there planned tasks that are missing from the changes?
- Are there changes that go beyond the plan's scope?

### 3d. Read the Branch Name

Run `git branch --show-current`. Branch names often encode intent
(e.g. `feat/add-retry-logic`, `fix/null-pointer-in-handler`).

### 3e. Summarize the Inferred Motivation

Write a brief summary (2-4 sentences) of what you believe the changes are trying
to accomplish and why. This becomes the lens through which you review.

## Step 4: Review the Changes

Now review the diff with the inferred motivation as your primary frame of reference.
For each changed file, read the surrounding code (not just the diff) to understand
the full context.

### 4a. Motivation Alignment

- Do the changes achieve their apparent goal?
- Are there simpler ways to achieve the same goal?
- Is anything missing that would be needed to fully deliver the intent?
- Do the changes introduce scope creep beyond the apparent goal?

### 4b. Correctness

- Are there logic errors or off-by-one mistakes?
- Are error cases handled?
- Are edge cases covered?
- Could the changes cause regressions in existing functionality?

### 4c. Design & Architecture

- Do the changes respect the existing architecture and layering?
- Are abstractions appropriate (not too much, not too little)?
- Is there unnecessary coupling introduced?
- Are naming conventions followed?

### 4d. Tests

- Are there tests for the new/changed behavior?
- Do the tests cover meaningful scenarios (not just happy path)?
- Are the tests robust and not brittle?
- Run the test suite to confirm everything passes:

```
# Run the relevant test suite (adapt to the project's language)
# Go:     go test ./...
# JS/TS:  npm test
# Rust:   cargo test
# Python: pytest
```

### 4e. Code Quality

- Is the code readable and self-documenting?
- Are there leftover debug statements, TODOs, or commented-out code?
- Does the code follow the project's style conventions?
- Are imports organized properly?

### 4f. Security (if applicable)

- No hardcoded secrets or credentials
- Input validation present where needed
- No SQL injection, XSS, or similar vulnerabilities introduced

## Step 5: Produce the Review

Structure your review as follows:

```
## Code Review: {Brief Description of Changes}

### Motivation
{Your inferred motivation summary from Step 3e}

### Verdict
✅ Approved / ⚠️ Approved with suggestions / ❌ Changes requested

### Critical Issues
{Issues that must be fixed — correctness bugs, security problems, data loss risks}

### Suggestions
{Improvements that would make the code better but are not blocking}

### Observations
{Neutral notes — things you noticed, questions, or praise for good patterns}

### Test Results
- Build: ✅ passing / ❌ failing
- Tests: ✅ passing / ❌ failing ({N} tests, {M} failures)
```

## Rules

- **Do NOT make changes to the code** — this is a read-only review
- **Always run the tests** — do not skip verification
- **Be specific** — reference exact file paths and line numbers
- **Be constructive** — suggest alternatives, don't just criticize
- **Respect the motivation** — review against intent, not your preferences
- **If unsure about intent, say so** — it's better to ask than to misinterpret
