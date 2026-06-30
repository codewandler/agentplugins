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

3. **Create the doc.** If it doesn't already exist, write `docs/designs/<slug>.md` from
   `${CLAUDE_PLUGIN_ROOT}/templates/design.md` (locate templates as in `/track:init`). Substitute
   `{{TITLE}}` (the story title), `{{PILLAR}}` (the story's pillar), and `{{STORY_LINKS}}` (a link back
   to the story file). Draft `## Why` and `## Approach` from the story's Goal/Acceptance as a starting
   point for the user to refine. If the file already exists, don't overwrite — just link to it.

4. **Link from the story.** Set the story's frontmatter `design: docs/designs/<slug>.md`.

5. **Report** the design doc path and that the story now points at it. Note that non-trivial work
   should have its design reviewed before implementation begins.
