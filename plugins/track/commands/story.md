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
   - **areas** — optional query-only subsystem tags such as `flux-lang`, `flux-flow`, `website`, `cli`,
     or `plugins`. Write them as an inline list: `areas: [flux-lang, flux-flow]`.

4. **Create through Flux.** Use the stable mutation path, repeating `--area` as needed:

   ```bash
   flux board create --kind story --id <ID> --title "<TITLE>" --pillar "<PILLAR>" \
     --status <backlog|ready> [--priority N] [--epic SLUG] [--area AREA] --output json
   ```

   Omit `--id` only when the repository uses Flux's default `C-N` allocator. Flux uses create-new
   semantics and never clobbers a competing allocation. Draft the generated `## Goal` and
   `## Acceptance` only after creation when the user supplied enough detail.

5. **Sync the board.** Run `flux board render --output json`.

6. **Report** the new story path and ID, and remind the user to flesh out `## Goal` and `## Acceptance`.

## Guardrails
- Never reuse or renumber an existing ID. If the computed filename already exists, bump the number.
- Flux is the only creation/render mutation path; do not copy templates or hand-edit the marker.
