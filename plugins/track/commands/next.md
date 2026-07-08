---
description: Report the top ready story to work on next, optionally filtered by area, with its Goal and Acceptance.
argument-hint: "[area]"
---

# /track:next

Identify and report the next story to work on. If `$ARGUMENTS` is present, treat it as an optional
`areas` filter (for example, `/track:next flux-lang` selects the top ready story tagged with
`areas: [flux-lang]`).

## Steps

1. **Read the stories.** Scan `docs/stories/*.md` (skip `README.md`, `_TEMPLATE.md`) and parse each
   one's frontmatter.

2. **Pick the top `ready` story.** Among stories with `status: ready`, choose the one with the lowest
   `priority` integer (ties break on `id`). If `$ARGUMENTS` names an area, consider only stories whose
   `areas` inline list contains that exact slug. If no ready story matches, say so and report any
   matching `in-progress` stories plus the size of the matching `backlog`.

3. **Present it.** Show the chosen story's `id`, `title`, `## Goal`, and `## Acceptance` checklist, the
   path to the file, and any linked `design:`.

4. **Offer to start.** Ask whether to begin. If yes:
   - set the story's `status: in-progress` and run `/track:board`; then
   - either implement it directly following the story's Acceptance, or delegate to the
     `story-implementer` agent for an end-to-end pass (failing-first test → gate → status).

Respect the standing rule: if the user has already named a different story or task, that takes
precedence over the board's top pick.
