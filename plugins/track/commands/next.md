---
description: Report the top ready story to work on next, with its Goal and Acceptance, and offer to start it.
argument-hint: ""
---

# /track:next

Identify and report the next story to work on.

## Steps

1. **Read the stories.** Scan `docs/stories/*.md` (skip `README.md`, `_TEMPLATE.md`) and parse each
   one's frontmatter.

2. **Pick the top `ready` story.** Among stories with `status: ready`, choose the one with the lowest
   `priority` integer (ties break on `id`). If there are none, say so and report any `in-progress`
   stories (work already underway) and the size of the `backlog`.

3. **Present it.** Show the chosen story's `id`, `title`, `## Goal`, and `## Acceptance` checklist, the
   path to the file, and any linked `design:`.

4. **Offer to start.** Ask whether to begin. If yes:
   - set the story's `status: in-progress` and run `/track:board`; then
   - either implement it directly following the story's Acceptance, or delegate to the
     `story-implementer` agent for an end-to-end pass (failing-first test → gate → status).

Respect the standing rule: if the user has already named a different story or task, that takes
precedence over the board's top pick.
