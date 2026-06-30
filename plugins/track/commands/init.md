---
description: Scaffold the track backlog framework (vision/roadmap/stories/designs + board + AGENTS.md wiring) into this repo. Idempotent and non-destructive.
argument-hint: "[docs-dir]"
---

# /track:init

Scaffold the **track** framework into the current repository. `$1` is the docs directory (default
`docs`). This is **idempotent and must never clobber existing files** — read before you write, and ask
the user before overwriting anything that already exists.

The plugin's templates are at `${CLAUDE_PLUGIN_ROOT}/templates/` (this token is substituted to the
real plugin path when the command runs). If for any reason it didn't resolve, locate the dir with
`find ~/.claude/plugins -path '*/track/templates' -type d 2>/dev/null | head -1`.

## Steps

1. **Survey.** Let `DOCS` = `$1` or `docs`. Check what already exists: `DOCS/README.md`,
   `DOCS/vision.md`, `DOCS/roadmap.md`, `DOCS/stories/`, `DOCS/stories/README.md`,
   `DOCS/stories/_TEMPLATE.md`, `DOCS/designs/`, `DOCS/archive/`, `CHANGELOG.md`, `AGENTS.md`. Report
   the survey.

2. **Confirm scope.** The **stories board** is always scaffolded. Ask the user which optional layers to
   add, defaulting to **everything not already present**: the `DOCS/README.md` docs map, `vision.md`,
   `roadmap.md`, `designs/`, `archive/`, `CHANGELOG.md`, and the `AGENTS.md` "Start here" wiring. Skip
   anything that already exists (never overwrite); if a target exists, leave it untouched and note it.

3. **Create the stories layer.**
   - `DOCS/stories/_TEMPLATE.md` ← `templates/story.md`.
   - `DOCS/stories/README.md` ← `templates/board.md`, substituting `{{PROJECT}}` with the repo name
     (infer from the directory or `package.json`/`Cargo.toml`/git remote).

4. **Create the optional layers** the user chose, substituting `{{PROJECT}}` (and leaving the
   `{{EXAMPLE_EPIC_*}}` placeholders for the user to fill or delete):
   - `DOCS/README.md` ← `templates/docs-readme.md` (the docs map).
   - `DOCS/vision.md` ← `templates/vision.md`
   - `DOCS/roadmap.md` ← `templates/roadmap.md`
   - `DOCS/designs/` ← create the directory (add a `.gitkeep` if empty).
   - `DOCS/archive/` ← create the directory (add a `.gitkeep` if empty) for superseded designs/notes.
   - `CHANGELOG.md` ← a minimal Keep-a-Changelog header if absent.

5. **Wire AGENTS.md.** If the user opted in: append the contents of `templates/agents-snippet.md` to
   `AGENTS.md` (create the file with a short title if it doesn't exist). The snippet is fenced by
   `<!-- BEGIN track:agents -->` / `<!-- END track:agents -->` — **if those markers already exist in
   AGENTS.md, replace the region between them** rather than appending a duplicate.

6. **Seed the board.** Run `/track:board $1` so the board's generated region is populated (it will show
   empty sections until stories exist).

7. **Report.** List exactly what was created vs. skipped, and tell the user the next step is
   `/track:story` to add their first story.

## Guardrails
- Never overwrite an existing file without explicit user confirmation. Treat all existing content as
  precious.
- Substitute placeholders (`{{PROJECT}}`, `{{TITLE}}`, …) — don't leave raw `{{…}}` tokens in created
  files except the optional `{{EXAMPLE_EPIC_*}}` ones in the roadmap, which you should point out.
