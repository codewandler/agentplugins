---
description: Report the top ready story to work on next, optionally filtered by area, with its Goal and Acceptance.
argument-hint: "[area]"
---

# /track:next

Identify and report the next story to work on. If `$ARGUMENTS` is present, treat it as an optional
`areas` filter (for example, `/track:next flux-lang` selects the top ready story tagged with
`areas: [flux-lang]`).

## Steps

1. **Ask Flux.** Run `flux board next --limit 1 [--area AREA] --output json`. It resolves ready state,
   dependency satisfaction, integer priority, natural-id ties and workspace namespacing from the
   authoritative board backend.

3. **Present it.** Show the chosen story's `id`, `title`, `## Goal`, and `## Acceptance` checklist, the
   path to the file, and any linked `design:`.

4. **Offer to start.** Ask whether to begin. If yes:
   - run `flux board start <ID> --output json` and `flux board render --output json`; then
   - either implement it directly following the story's Acceptance, or delegate to the
     `story-implementer` agent for an end-to-end pass (failing-first test → gate → status).

Respect the standing rule: if the user has already named a different story or task, that takes
precedence over the board's top pick.
