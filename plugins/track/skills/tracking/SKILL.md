---
name: tracking
description: >-
  Spec-driven backlog and roadmap discipline for a repo. Use when the user mentions stories,
  the backlog, the board, epics, a roadmap, "what should I work on / what's next", picking up
  or closing a story, or when the repo has a docs/stories/ directory. Teaches the four-layer
  model (vision -> roadmap -> stories -> designs), the story frontmatter schema and status
  lifecycle, how the status board is generated, and how to self-orient and pick up the next
  ready story. Pairs with the /track:* slash commands.
---

# Track — spec-driven backlog

This repo (or one you are scaffolding) uses **track**: a lightweight, in-repo planning framework
where every unit of work is a markdown **story** with frontmatter, and a **status board** is
generated deterministically from those stories. The model proven in the `flux` project, packaged so
any agent can self-orient and keep the backlog honest.

## The four layers

| Layer | Lives in | What it is |
|---|---|---|
| **Vision** | `docs/vision.md` | Why the project exists and the principles that break ties. Stable. |
| **Roadmap** | `docs/roadmap.md` | Status, what's delivered, what's next, and **epic** narratives. |
| **Stories** | `docs/stories/<ID>-<slug>.md` + `README.md` (the **board**) | The operational unit. One file per story; the board indexes them by status. |
| **Designs** | `docs/designs/<slug>.md` | Design records for non-trivial stories and epics. |

Plus: `CHANGELOG.md` (done stories roll up here) and `docs/archive/` (superseded material).

## Self-orient at the start of a session

1. Run `git status --short --branch`. Treat uncommitted changes as user-owned unless you made them.
2. If the user named a story, file, or task, **that** scopes the work.
3. Otherwise open the board (`docs/stories/README.md`) and take the **top `ready` story by
   `priority`** (lower integer = higher priority). `/track:next` reports it for you.
4. Read that story's `## Goal` and `## Acceptance` — they define what "done" means. If it links a
   `design:`, read it.

## Story lifecycle

`backlog` → `ready` → `in-progress` → (`blocked`) → `done`

- Set `status: in-progress` when you start; keep the `## Progress` log current so a resuming agent
  knows exactly where things stand.
- A behavioral change ships with a **failing-first test** named in `## Acceptance`.
- Non-trivial work gets a design doc first (`/track:design <ID>`).
- On done: `/track:done <ID>` sets `status: done`, adds a CHANGELOG entry, and regenerates the board.

## The board is generated — never hand-edit the generated region

The board's status lists live between `<!-- BEGIN track:board -->` and `<!-- END track:board -->`.
**After any change to a story's `status`, `priority`, `title`, or `epic`, regenerate the board** with
`/track:board`. Everything outside the markers (intro, status summary, epic narratives) is
hand-written and preserved. Story frontmatter is the single source of truth; the board is a view.

## Frontmatter (the contract)

```yaml
---
id: D-12              # pillar/prefix letter(s) + number; unique across the repo
title: Short imperative title
pillar: Core          # optional project legend (e.g. Agent | Language | Improve | Core)
status: ready         # backlog | ready | in-progress | blocked | done
priority: 1           # integer rank among `ready` stories (lower = higher); omit otherwise
design:               # optional path: docs/designs/<slug>.md
epic:                 # optional epic slug; groups this story on the board + roadmap
---
```

See `references/frontmatter.md` for the full field reference, `references/board-format.md` for the
board structure and generation rules, and `references/workflow.md` for the per-session loop.

## Commands

| Command | Does |
|---|---|
| `/track:init` | Scaffold the framework into the current repo (idempotent, never clobbers). |
| `/track:story` | Create a new story (allocates the next ID, drops it in `docs/stories/`, syncs the board). |
| `/track:epic` | Create an epic: a design doc + a roadmap narrative + (optionally) child stories. |
| `/track:board` | Regenerate the board from story frontmatter. |
| `/track:next` | Report the top `ready` story and offer to start it. |
| `/track:done` | Close a story: status, CHANGELOG entry, board sync. |
| `/track:design` | Create/link a design doc for a story. |

## Rules

- Frontmatter is the source of truth; the board is derived. Keep them in sync via `/track:board`.
- Create a story for any new or unscoped work so the next agent inherits the context.
- Don't invent a new status or ID scheme — match what the existing stories use.
- Never commit without an explicit instruction from the user.
