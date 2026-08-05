---
description: Create or link a design doc for a story and set its design frontmatter field.
argument-hint: "<ID> [slug]"
---

# /track:design

Create a design doc for a story and wire it up. `$1` is the story ID; `$2` (optional) is the design
slug.

## Steps

1. **Find the story.** Locate `docs/stories/<ID>-*.md` (from `$1`). If `$1` is empty, ask. Read its
   `## Goal` and `## Acceptance` so the design starts grounded.

2. **Determine the slug.** Use `$2` if given, else derive one from the story title (lowercase, hyphen-
   joined). The design doc will be `docs/designs/<slug>.md`.

3. **Create through Flux.** Flux uses create-new semantics and refuses an existing id:

   ```bash
   flux board design create <slug> --title "<TITLE>" --content "<DRAFT>" --output json
   ```

4. **Link through Flux.** `flux board design link <slug> <ID> --output json`.

5. **Report** the design doc path and that the story now points at it. Note that non-trivial work
   should have its design reviewed before implementation begins.
