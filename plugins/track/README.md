# track — spec-driven backlog for Claude Code

A reusable Claude Code plugin that brings a proven, lightweight **project-tracking framework** to any
repository: work is captured as in-repo markdown **stories**, and a status **board** is generated
**deterministically** from those stories. Modeled on the system the
[`flux`](https://github.com/codewandler/flux) project uses to keep agents and humans oriented, then
packaged so any agent self-orients and picks up the next ready story.

## The model

Four layers, all plain markdown in your repo:

```
docs/
  README.md            # the docs map — where to find everything
  vision.md            # why the project exists + principles (the tie-breaker)
  roadmap.md           # status, what's next, epic narratives
  stories/
    README.md          # the board — generated from frontmatter
    <ID>-<slug>.md      # one file per story (frontmatter is the source of truth)
    _TEMPLATE.md
  designs/<slug>.md     # design records for non-trivial stories & epics
  archive/             # superseded designs / notes
CHANGELOG.md           # released history
```

A story's frontmatter (`id`, `title`, `status`, `priority`, optional `pillar`/`design`/`epic`/`note`)
is the **single source of truth**; the board is a generated view. The generated board carries per-row
annotations (`note`), one-line epic blurbs (pulled from each epic's design doc), and a Done list — so
it stays as context-rich as a hand-curated board, without anyone hand-editing it. The "Start here"
loop (written into your `AGENTS.md` by `/track:init`) makes every agent read the board and take the
top `ready` story.

## Install

```
/plugin marketplace add codewandler/agentplugins
/plugin install track@agentplugins
```

Installs into user scope (`~/.claude/plugins/`), so it's available in **all** your projects. Others
reuse it with the same two commands. For team-wide auto-install, add to a repo's `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "agentplugins": { "source": { "source": "github", "repo": "codewandler/agentplugins" } }
  },
  "enabledPlugins": { "track": true }
}
```

## Commands

| Command | Does |
|---|---|
| `/track:init [docs-dir]` | Scaffold the framework into the current repo (idempotent; never clobbers). |
| `/track:story [title]` | Create a story — allocates the next ID, writes the file, syncs the board. |
| `/track:epic [name]` | Start an epic — a design doc + roadmap narrative + optional child stories. |
| `/track:board [docs-dir]` | Regenerate the board from story frontmatter. |
| `/track:next` | Report the top `ready` story and offer to start it. |
| `/track:done <ID>` | Close a story — set `status: done`, add a CHANGELOG entry, sync the board. |
| `/track:design <ID> [slug]` | Create/link a design doc for a story. |

The `tracking` skill auto-activates when you mention stories, the backlog, the roadmap, epics, or ask
"what's next" — it teaches the conventions so the commands aren't even strictly required. The
`story-implementer` agent implements a single story end-to-end (failing-first test → gate → status).

## Board generation

`/track:board` runs `scripts/gen_board.py` (Python 3, **standard library only** — no install step). It
reads every story's frontmatter and rewrites only the region between `<!-- BEGIN track:board -->` and
`<!-- END track:board -->` in `docs/stories/README.md`, grouping by status (Now / Next / Blocked /
Backlog / Done) and by `epic`. If `python3` isn't available, the command regenerates the board by
following `scripts/BOARD_SPEC.md`, which specifies the exact same output. The hand-written parts of the
board (intro, status summary, epic narratives) are always preserved.

## License

MIT
