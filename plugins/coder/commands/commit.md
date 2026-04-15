---
description: Create a well-formed git commit from staged or unstaged changes
aliases: [ci]
---

# Commit Workflow

Follow these steps to create a well-formed commit from the current changes.

## Step 1: Assess the Current State

Run `git status` and `git diff --stat` to understand what has changed.
If there are no changes, tell the user and stop.

## Step 2: Review the Git History for Conventions

Run `git log --oneline -10` to understand the repository's commit style:
- Semantic prefixes? (feat:, fix:, chore:, refactor:, docs:, test:, ci:, style:)
- Casing and format of commit titles
- Whether ticket refs appear in titles or taglines
- Level of detail in commit bodies

Adopt the repository's existing conventions exactly.

## Step 3: Analyse the Changes

Run `git diff` (or `git diff --cached` if changes are staged) to understand the
actual code changes. Group them logically:

- Are these changes all related to one concern, or multiple?
- If multiple concerns: propose splitting into separate atomic commits.
- Each commit should be a single logical unit that could be reverted independently.

## Step 4: Update CHANGELOG.md (if it exists)

Check whether a `CHANGELOG.md` file exists in the repository root.

If it exists:
- Read the existing file to understand the format and conventions in use
  (Keep-a-Changelog, date headers, semantic sections, etc.).
- Add an entry for the changes being committed under the appropriate section
  (e.g. `Added`, `Changed`, `Fixed`, `Removed`).
- If the file has an `[Unreleased]` section, add the entry there.
  Otherwise create one above the latest release.
- Keep the entry concise: one line per logical change, written for a human
  reader (not a diff summary).

If no `CHANGELOG.md` exists, skip this step silently.

## Step 5: Stage Appropriately

If changes span multiple concerns, use `git add -p` or `git add <file>` to stage
only the files/hunks for the first logical commit. Explain what you're staging and why.

If all changes belong together, `git add -A` is fine.

Include the `CHANGELOG.md` update in the same stage as the changes it documents.

## Step 6: Write the Commit Message

### Title Line (first line)
- Use the repository's commit convention (semantic prefixes if they use them)
- Max 72 characters
- Imperative mood ("Add feature" not "Added feature")
- No trailing period
- NO ticket references in the title

### Body (after blank line)
- Explain **what** changed and **why** (not how — the diff shows how)
- Use bullet points for multiple changes
- Wrap lines at 72 characters
- Include context that wouldn't be obvious from the diff alone

### Taglines (after body)
- Ticket references go in a `Refs:` tagline: `Refs: DEV-123`
- Co-authors go in `Co-authored-by:` taglines
- Breaking changes: `BREAKING CHANGE: description`

### Example

    feat: add retry logic for transient API failures

    - Added exponential backoff with jitter for 429/503 responses
    - Default max retries: 3, configurable via RetryConfig
    - Existing callers are unaffected (retry is opt-in)

    Refs: DEV-456

## Step 7: Commit

Run `git commit` with the prepared message. Show the result.

## Step 8: Verify

Run `git log -1 --format=fuller` to confirm the commit looks correct.
Show the output to the user.

## Rules

- **NEVER amend or rebase without explicit user instruction**
- **NEVER force-push**
- **If unsure about grouping, ask the user before committing**
- **Prefer multiple small commits over one large commit**
