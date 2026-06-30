# Story frontmatter — full reference

Every story file is `docs/stories/<ID>-<slug>.md` and opens with a YAML frontmatter block fenced by
`---`. The frontmatter is the **single source of truth**; the board and (optionally) roadmap status
are views derived from it.

## Fields

| Field | Required | Type | Meaning |
|---|---|---|---|
| `id` | yes | string | Unique identifier, `<PREFIX>-<N>` (e.g. `D-12`, `A-3`). The prefix is the pillar/track letter(s); the number is allocated in sequence per prefix. Must be unique across all stories. |
| `title` | yes | string | Short imperative title. Shown verbatim on the board. |
| `pillar` | no | string | Optional project legend the board echoes (e.g. `Agent`, `Language`, `Improve`, `Core`). Omit if the project has no pillars. |
| `status` | yes | enum | One of `backlog`, `ready`, `in-progress`, `blocked`, `done`. Drives which board section the story lands in. |
| `priority` | when `ready` | integer | Rank among `ready` stories — **lower = higher priority** (1 is the top pick). Omit for non-ready stories. Ties break on `id`. |
| `design` | no | path | Repo-relative path to a design doc, e.g. `docs/designs/endpoint-discovery.md`. |
| `epic` | no | slug | Groups the story under an epic on the board and roadmap. The slug should match a design doc basename in `docs/designs/<epic>.md` so the epic title can be resolved from that doc's H1. |

## ID / prefix scheme

- The prefix is a short letter or letter-group identifying the pillar or track. `flux` uses
  `A` (Agent), `L` (Language), `I` (Improve), `C` (Core). A project with no pillars can use a single
  prefix like `S` (Story) or `T` (Task).
- `/track:story` infers the existing prefixes from the stories already present and allocates the next
  number for the chosen prefix. Don't renumber existing stories.

## Status lifecycle

```
backlog ──promote──▶ ready ──start──▶ in-progress ──finish──▶ done
                       ▲                   │
                       └─── unblock ◀── blocked ◀── block
```

- `backlog` — captured but not yet scheduled. No `priority`.
- `ready` — scheduled; carries a `priority`. The board sorts these into the **Next** list.
- `in-progress` — actively being worked. Appears in **Now**. Keep `## Progress` current.
- `blocked` — cannot proceed; note the blocker in `## Notes`.
- `done` — complete and verified. Rolls into `CHANGELOG.md`; the board drops it from the active lists.

## Body sections

```markdown
# <title>

## Goal
One or two sentences: the outcome this delivers and which value/pillar it serves.

## Acceptance
- [ ] A testable criterion. A behavioral change names the failing-first test that proves it.
- [ ] …

## Progress
- (running log / checklist — a resuming agent reads this to know exactly where things stand)

## Notes
- Links, blockers, design pointers, relevant files.
```
