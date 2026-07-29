# Changelog

All notable changes to codewandler/agentplugins are documented in this file.

## [Unreleased]

## [0.6.1] - 2026-07-29

### Changed

#### Track Plugin (0.4.1)

- **`impl-coord` — disk is now a running budget, not a one-time check.** Real multi-wave runs
  exhaust disk: each worktree pays its own cold build, the integration tree's `target/` balloons
  across repeated gates, and on some toolchains ENOSPC surfaces as opaque compiler/linker errors
  rather than "disk full". §1.7 now tells the coordinator to reclaim *before* fanning out when space
  is already tight, and §4.7 makes disk reclamation part of the integration loop — `git worktree
  remove` + `git worktree prune` after each integration, and `cargo clean` the integration tree
  between waves when free space tightens (it is rebuilt cold at the next gate regardless). Both carry
  an explicit guard: never `cargo clean` or remove a worktree that still holds an unreviewed,
  unmerged, or parked diff.

## [0.6.0] - 2026-07-29

### Added

#### Track Plugin (0.4.0)

- **`impl-coord` — autonomous backlog coordination.** A new skill that works the backlog as
  fan-out waves instead of one story at a time: it selects independent `ready` stories via a
  fail-closed disjointness test (biasing toward freshly review-derived epics/stories), dispatches
  each to an isolated worktree implementor, reviews returned diffs as evidence (re-running the
  claimed failing-first test against the merge base), and integrates serially with the project's
  full gate run after every `--no-ff` merge. Shared ledgers (CHANGELOG, board, roadmap, lockfiles)
  are fenced to the coordinator, which is what makes stories independent at all. Bounded autonomy:
  the skill invocation authorizes worktrees, implementor commits, merges and ledger edits — never a
  push, tag, release, or history rewrite. Design rationale in `skills/impl-coord/DESIGN.md`.
- **`story-impl` agent** — implements exactly one story inside its own git worktree on a scratch
  `impl/<ID>` branch: failing-first test, implementation, full gate until green, commits on its
  branch, and a structured, parseable handoff report. Never touches the main branch, never pushes,
  never edits fenced ledgers. (The existing `story-implementer` remains the single-story,
  main-tree, no-commit variant.)
- **`story-review` agent** — independent read-only second review, spawned when a diff touches the
  project's safety envelope (auth/permissions, secret handling, dispatch chokepoints, declared
  safety invariants, published public APIs). Grades against declared invariants with
  `path:line` evidence and returns a PASS/REWORK/PARK verdict; it changes nothing.

Extracted and generalized from the flux repo's in-repo coordinator (its repo-local skill, agents,
and design record moved here); marketplace bumped to 0.6.0.

## [0.5.0] - 2026-07-09

### Added

#### Track Plugin (0.3.0)

- **Query-only story areas.** Stories can now carry optional subsystem tags such as
  `areas: [flux-lang, flux-flow]`; the board keeps its existing row format, while `/track:next
  <area>` and documented `rg` queries can select stories mostly concerned with a subsystem.

## [0.4.0] - 2026-07-08

### Added

#### rust-pro Plugin (0.1.0)

- **`rust-pro`** — an idiomatic-Rust specialist skill packaged as an installable plugin. A compact
  `SKILL.md` (role, when-to-use, workflow, MUST/MUST-NOT constraints) routes via progressive
  disclosure to six code-heavy references:
  - `ownership.md` — move/Copy/borrow/clone, lifetimes & elision, `Box`/`Rc`/`Arc`/`RefCell`/`Cow`, `Weak` cycles.
  - `error-handling.md` — `Result`/`?`, `thiserror` (libraries) vs `anyhow` (apps), the `Error` contract, panic policy.
  - `traits-generics.md` — trait design, static vs `dyn` dispatch, dyn compatibility, conversions, builder & typestate, async traits.
  - `async-concurrency.md` — Tokio, `Send`/`Sync`, channels, `select!`/`JoinSet`, `rayon`, scoped threads, the no-lock-across-`.await` rule.
  - `testing.md` — unit/integration/doc tests, `nextest`, `proptest`, `criterion`, Miri, `unsafe` review.
  - `project-structure.md` — Cargo workspaces, feature flags, MSRV/resolver v3, `clippy`/`rustfmt`, edition-2024 changes, release profiles.
- Content researched against the **Rust 2024 edition** (shipped with Rust 1.85) and the mid-2026
  ecosystem: `async fn` in traits stable but not `dyn`-compatible, async-std discontinued
  (RUSTSEC-2025-0052) with Tokio the default runtime, built-in `#[bench]` removed from stable, and
  lints centralized via the `[lints]` table.
- Registered in `.claude-plugin/marketplace.json` (marketplace bumped to 0.4.0); root `README.md`
  updated with install instructions and the reference map.

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

[0.5.0]: https://github.com/codewandler/agentplugins/releases/tag/v0.5.0
[0.4.0]: https://github.com/codewandler/agentplugins/releases/tag/v0.4.0
[0.3.0]: https://github.com/codewandler/agentplugins/releases/tag/v0.3.0
[0.2.0]: https://github.com/codewandler/agentplugins/releases/tag/v0.2.0
[0.1.0]: https://github.com/codewandler/agentplugins/releases/tag/v0.1.0
