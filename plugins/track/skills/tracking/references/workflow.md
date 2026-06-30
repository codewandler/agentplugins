# The working loop

This is the per-session loop a `track`-enabled repo expects. It mirrors the "Start here" contract
that `/track:init` writes into `AGENTS.md`, so any agent that reads either one behaves consistently.

## Start here (every session)

1. **Orient** — read the latest user request, then run `git status --short --branch`. Treat
   uncommitted changes as user-owned unless you made them; never reset/discard/force-push them
   without an explicit instruction.
2. **What to work on** — if the user named work, do that. Otherwise open the board
   (`docs/stories/README.md`) and take the top `ready` story by `priority`. `/track:next` reports it.
3. **The contract** — read the story's `## Goal` and `## Acceptance`. Acceptance defines "done". If
   it links a `design:`, read that too.
4. **Set status** — mark the story `in-progress` (and `/track:board`).
5. **Do the work** — non-trivial design goes in `docs/designs/` first (`/track:design <ID>`);
   implement; satisfy each Acceptance item; a behavioral change ships with a **failing-first test**;
   run the project's gate (tests / lint / format) until green.
6. **On done** — `/track:done <ID>`: set `status: done`, add a CHANGELOG entry, regenerate the board.
   Keep design/plan docs in sync.
7. **New or unscoped work?** Create a story first (`/track:story`) so the next agent inherits the
   context.

## Discipline

- **One source of truth.** Story frontmatter drives the board. After any status/priority/title/epic
  change, run `/track:board`.
- **Auditability.** Non-trivial behavior gets a story, a design (if warranted), a failing-first test,
  and a CHANGELOG entry.
- **Don't commit without an explicit instruction.** When you do commit, match the repo's existing
  commit conventions (run `git log --oneline -10` first).
- **Keep the gate green.** A change isn't done until the project's tests/lint/format pass.
