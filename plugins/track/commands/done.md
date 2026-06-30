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

3. **Set status.** Update the frontmatter to `status: done`. Remove any now-irrelevant `priority`.

4. **Roll into the changelog.** Append an entry to `CHANGELOG.md` (create it with a Keep-a-Changelog
   header if absent). Match the file's existing format; under an `Unreleased`/current section add a
   one-line summary: `**<ID>** — <title>: <what shipped, briefly>`. Read the existing changelog first
   to match its conventions exactly.

5. **Regenerate the board.** Run `/track:board` — the story drops out of the active lists and the Done
   count increments.

6. **Offer follow-ups.** If the story links a `design:` that is now fully realized, offer to move it to
   `docs/archive/designs/`. Ask whether there's follow-on work to capture as a new story
   (`/track:story`).

7. **Report** what changed: status, the CHANGELOG line, and the board update. Do not commit unless the
   user explicitly asks.
