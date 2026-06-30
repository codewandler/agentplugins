---
description: Start an epic — create its design doc, add a roadmap narrative, and optionally seed child stories grouped by the epic slug.
argument-hint: "[epic name]"
---

# /track:epic

Create an **epic**: a themed group of stories with a shared design doc. `$ARGUMENTS` (if given) is the
epic name. An epic is lightweight — it's a design doc plus an `epic: <slug>` link on its member
stories; the board groups those stories automatically.

## Steps

1. **Name + slug.** Take the epic name from `$ARGUMENTS` or ask. Derive a `<slug>` (lowercase, hyphen-
   joined) — this slug is the join key: it must match the design doc basename `docs/designs/<slug>.md`
   and the `epic:` field on member stories.

2. **Create the design doc.** Write `docs/designs/<slug>.md` from `${CLAUDE_PLUGIN_ROOT}/templates/design.md`
   (locate templates as in `/track:init`). Substitute `{{TITLE}}` with the epic name and `{{PILLAR}}`;
   set `{{STORY_LINKS}}` to a placeholder (you'll fill it as stories are created). Fill in `## Why` and
   `## Approach` with the user's description of the epic. The H1 of this file becomes the epic's title
   on the board, so make it read well (a leading `Design:` is stripped automatically).

3. **Add a roadmap narrative.** If `docs/roadmap.md` exists, add (or update) a `### <Epic title>`
   subsection under its `## Epics` heading: a short paragraph on why the epic exists and what "done"
   looks like, linking the design doc. This is hand-written narrative — the board's generated lists
   reference it by grouping the member stories under the same title.

4. **Seed child stories (optional).** Ask whether to create the epic's initial stories now. For each,
   run the `/track:story` flow and set `epic: <slug>` in the frontmatter. Then update the design doc's
   `## Stories` / `{{STORY_LINKS}}` to link them.

5. **Sync the board.** Run `/track:board` — member stories now appear grouped under the epic title in
   the Next/Backlog sections.

6. **Report** the design doc path, the slug (so the user can tag more stories with `epic: <slug>`), and
   any seeded stories.
