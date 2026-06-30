# Changelog

All notable changes to codewandler/agentplugins are documented in this file.

## [0.3.0] - 2026-06-30

### Changed

#### Track Plugin (0.2.0) — board richness

The generated board is now a strict superset of a hand-curated one:

- **Per-row annotations**: new optional `note:` story frontmatter field, rendered after the title on
  the board (`· <note>`). Richness lives in the source of truth, not in stale hand-edited prose.
- **Epic blurbs**: each `### <epic>` group now shows a one-line blurb pulled from the first line under
  the epic design doc's `## Why`.
- **Done list**: the Done section now lists done stories (id — title · note) plus a CHANGELOG pointer,
  instead of just a count.
- **Docs map**: `/track:init` now scaffolds a `docs/README.md` navigation map and a `docs/archive/`
  directory for superseded material.

`scripts/gen_board.py`, `scripts/BOARD_SPEC.md`, the templates, the `tracking` skill, and the
references were updated together; re-validated with `claude plugin validate --strict`.

## [0.2.0] - 2026-06-30

### Added

#### Marketplace

- **`.claude-plugin/marketplace.json`** — the repo is now an installable Claude Code marketplace
  (`agentplugins`). Add it with `/plugin marketplace add codewandler/agentplugins`.

#### Track Plugin

- **`track`** — a spec-driven backlog plugin: a four-layer in-repo framework (vision → roadmap →
  stories → designs) with a status board generated deterministically from story frontmatter. Modeled
  on the tracking system used by the `flux` project.
  - **Commands**: `init`, `story`, `epic`, `board`, `next`, `done`, `design` (namespaced `/track:*`).
  - **Skill**: `tracking` — self-orientation + conventions (four-layer model, frontmatter schema,
    status lifecycle, board rules), with progressive-disclosure references.
  - **Agent**: `story-implementer` — implements a single story end-to-end (failing-first test → gate →
    status), without committing.
  - **Board generator**: `scripts/gen_board.py` (Python 3, stdlib-only, deterministic, idempotent)
    plus `scripts/BOARD_SPEC.md` for an exact agent-driven fallback when Python is unavailable.
  - **Templates**: story, board, roadmap, vision, design, and an `AGENTS.md` "Start here" snippet.
- Validated with `claude plugin validate --strict` (plugin + marketplace) and exercised end-to-end
  against the `flux` repo's real story corpus.

### Notes

- The existing `coder` content is left untouched and is not yet registered in the marketplace (it
  uses a pre–Claude-Code format and has no `plugin.json`).

## [0.1.0] - 2025-04-16

### Added

#### Coder Plugin
- **Core Skill**: `coder/SKILL.md` with agent identity and operating modes
  - Iron Laws (non-negotiable practices)
  - Operating modes (normal, readonly)
  - Tool management guidelines
  - Module system documentation

- **References** - Supporting materials for agent guidance
  - **Language Guides**: Go programming best practices
  - **Workflow Guides**:
    - Brainstorming techniques
    - Git worktree workflows
    - Plan writing and design
    - Subagent-driven development
    - Test-driven development
    - Code review requesting
    - Development branch finishing

- **Gitworktree Skill**: `gitworktree/SKILL.md` for version control workflows

#### Commands
- `commit.md` - Commit message and process guidelines
- `release.md` - Release procedures and versioning
- `review.md` - Code review standards and expectations
- `improve.md` - Continuous improvement and learning process
- `complain.md` - Feedback and complaint handling mechanism

### Structure

- Pure markdown content repository
- Claude plugin directory layout
- YAML frontmatter support for skill metadata
- Organized reference materials

### Status

✓ Initial extraction from flai  
✓ ~15 focused markdown files  
✓ Ready for agent system integration

---

[0.3.0]: https://github.com/codewandler/agentplugins/releases/tag/v0.3.0
[0.2.0]: https://github.com/codewandler/agentplugins/releases/tag/v0.2.0
[0.1.0]: https://github.com/codewandler/agentplugins/releases/tag/v0.1.0
