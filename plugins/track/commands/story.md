---
description: Create a new track story — allocate the next ID, write the story file from the template, and sync the board.
argument-hint: "[title]"
---

# /track:story

Create a new story. `$ARGUMENTS` (if given) is the story title.

## Steps

1. **Locate the stories dir.** Default `docs/stories/`. If it doesn't exist, tell the user to run
   `/track:init` first and stop.

2. **Learn the ID scheme.** Read the existing `*.md` story filenames + their frontmatter `id` and
   `pillar` fields. Determine the set of prefixes in use (e.g. `A`, `L`, `I`, `C`) and the highest
   number per prefix.

3. **Gather inputs.**
   - **Title** — from `$ARGUMENTS`, else ask.
   - **Pillar / prefix** — if multiple prefixes exist, ask which one (show the legend). If exactly one
     exists, use it. If none exist yet, ask the user for a prefix letter (suggest `S` for a generic
     "story" track) and the pillar label (optional).
   - **Status** — default `backlog`; offer `ready` (which needs a `priority`).
   - **priority** — only if `ready`: ask for the integer rank (lower = higher); default to one past the
     current max ready priority.
   - **epic** — optional; if the user names one, use its slug.

4. **Allocate the ID.** `<PREFIX>-<next number for that prefix>`. Build a slug from the title
   (lowercase, words joined by `-`, punctuation dropped).

5. **Write the file.** `docs/stories/<ID>-<slug>.md` from `templates/story.md` (resolve the templates
   dir as in `/track:init`), substituting `{{ID}}`, `{{TITLE}}`, `{{PILLAR}}` and setting `status`
   (and `priority`/`epic` if provided). Leave the body sections as prompts for the user to fill, or
   draft a first-pass `## Goal`/`## Acceptance` from the title if the user gave enough detail.

6. **Sync the board.** Run `/track:board`.

7. **Report** the new story path and ID, and remind the user to flesh out `## Goal` and `## Acceptance`.

## Guardrails
- Never reuse or renumber an existing ID. If the computed filename already exists, bump the number.
- Don't leave raw `{{…}}` placeholders in the created file.
