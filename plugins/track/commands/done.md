---
description: Close a story — set status to done, add a CHANGELOG entry, and regenerate the board.
argument-hint: "<ID>"
---

# /track:done

Close out a completed story. `$ARGUMENTS` is the story ID (e.g. `D-12`).

## Steps

1. **Find the story.** Locate `docs/stories/<ID>-*.md`. If `$ARGUMENTS` is empty, ask which story (or
   infer from the current `in-progress` story if there's exactly one). Read it.

2. **Sanity-check.** Confirm the `## Acceptance` items are actually satisfied. If any are unchecked,
   point them out and ask the user to confirm before proceeding — don't mark done prematurely.

3. **Complete atomically through Flux.** Supply the changelog text; if Acceptance is intentionally
   incomplete, require and record a concrete override reason:

   ```bash
   flux board done <ID> --changelog "**<ID>** — <title>: <what shipped>" \
     [--override-reason "<reason>"] --output json
   ```

   Flux checks Acceptance, removes priority, appends the changelog entry and regenerates the board.

4. **Offer follow-ups.** If the story links a `design:` that is now fully realized, offer to move it to
   `docs/archive/designs/`. Ask whether there's follow-on work to capture as a new story
   (`/track:story`).

5. **Report** what changed: status, the CHANGELOG line, and the board update. Do not commit unless the
   user explicitly asks.
