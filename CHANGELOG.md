# Changelog

All notable changes to codewandler/agentplugins are documented in this file.

## [Unreleased]

## [0.8.1] - 2026-08-01

### Fixed

#### Track Plugin (0.5.1)

**A dispatched implementor's worktree is not guaranteed to sit at the coordinator's `HEAD`**, and
nothing in either file said so. Observed across one wave of three: all three worktrees were created
from the commit *before* the coordinator's plan commit, so the story files it had just written and a
dependency it had just added under the fence were absent from every implementor's tree.

The failure is quiet and it misattributes. An agent reports that a file the brief names does not
exist, or that a "pre-added" dependency is missing — both read as coordinator error. Two of the
three recovered by branching from `main`'s tip on their own initiative; the third could not, because
`story-impl` forbids exactly that: *"never `git switch` to the main branch, never merge"*. It
improvised a substitute story file from the dispatch brief instead — good judgement under a rule
that left it no legal move, and work the coordinator then had to reconcile by hand at integration.

- **`story-impl` checks its base before it reads anything.** Step 1 now compares `git rev-parse
  HEAD` against `git rev-parse main` and names the symptom explicitly: a file the dispatch names but
  that does not exist is almost never an invented path, it is a stale base. An agent that does
  substitute something must lead `DEVIATIONS:` with it, because the coordinator has to reconcile it.
- **Step 2 branches from the tip**: `git switch -c impl/<ID> main`. Naming `main` as the start point
  creates the branch at the tip *without* checking `main` out, so the prohibition survives intact.
  An agent already committed on a stale branch merges `main` into it — never rebases — and the
  blanket "never merge" gains that one narrow exception, stated where the prohibition lives. The
  step ends with a verification, because `BASE_PROOF:` taken at an older base does not prove the
  test fails against the code being merged into.
- **The coordinator names the sha it dispatched from.** `§2 Dispatch` gains it as a required brief
  field — `git rev-parse HEAD`, read *after* the last commit — which turns a confusing absence into
  a check the implementor can run. Paired with two habits: commit ledger and setup work *then* read
  the sha *then* dispatch, and add a story's dependency yourself before dispatch (dependency lists
  are fenced) and say so. Plus the disposition rule: an implementor that improvised around a missing
  file has a wrong base, not a scope violation — send it the sha, have it merge and reconcile.

`story-implementer` is unaffected — it works in the main tree and has no worktree base to be stale.

## [0.8.0] - 2026-07-30

### Changed

#### Track Plugin (0.5.0)

Hardening pass over `impl-coord` driven by a meta-analysis of **18 real coordinator runs** across
three repos (flux, sipx, sipx-clstr) and the **887 subagent transcripts** under them — 116
`story-impl`, 21 `story-review`. Every change below closes a gap that was measured, not imagined.

The finding that shaped the rest: **rules that become artifacts survive; rules that stay procedures
decay.** The fence — an enumerable list copied into every dispatch — held at 169/169 (100%). The
mandated "re-run the failing-first test against the merge base", a procedure the coordinator had to
remember, ran in ~3% of dispatches; 14 of 18 sessions never did it once.

- **The merge-base proof is now an artifact, not a procedure.** `story-impl` must emit a
  `BASE_PROOF:` field: the exact command, run in its own worktree against
  `$(git merge-base main HEAD)`, with output showing the named test failing there. Absent, empty or
  passing at the base is an automatic REWORK. The coordinator reads a field and spot-checks it when
  the diff is in the safety envelope or the proof looks synthesised, instead of nominally re-running
  everything and actually re-running nothing. Both files carry the soundness caveat: a build cache
  shared across checkouts makes such a proof worthless while it still looks rigorous.
- **The autonomy boundary now splits reversible from irreversible.** `git push` of the current
  branch, annotated tags and a GitHub release are authorized; registry uploads
  (`cargo publish`, `npm publish`), force-push and history rewrites are not. The old boundary
  forbade the reversible half too, so a finished run stalled to ask permission — most of the 25
  `AskUserQuestion` calls observed were release-scope questions the skill gave no way to answer, and
  users authorized a push anyway in 9 of 18 sessions. The governing rule is stated once and reused:
  *do the reversible half, flag the irreversible half unrun.* New **§6 Cut a release** makes release
  scope a decision the skill covers.
- **New §7 degraded mode — when implementors cannot be spawned.** Roughly 1 subagent in 14 (63/887)
  died to infrastructure rather than to code: org and weekly spend limits, `529 Overloaded`,
  `Not logged in`. "The coordinator never implements" assumed implementors exist; with none
  available the model invented a fallback that dropped the branch, the isolation and the independent
  review, and in one run edited files inside a *live* implementor's worktree. The degraded path is
  now specified and keeps the audit trail: don't retry into the wall, commit a dead agent's loose
  work to its own branch, implement on `impl/<ID>` and route it through review and integration
  normally, spawn a reviewer on your own diff, and mark the story `coordinator-implemented` in the
  report table so the run stays honest about which diffs had one pair of eyes.
- **Both concurrency dials retuned.** Wave size becomes a budget — 3 by default, up to 5 when the
  user asks or `df` shows headroom for that many cold builds — after users asked for 5 in four
  separate sessions against a flat cap of 3. `story-review` is now spawned for every non-trivial
  diff and always for the safety envelope (the envelope is a floor, not a ceiling; 42 spawns across
  169 dispatches, with 4 sessions spawning none), the reviewer is told what the coordinator has
  *not* verified itself, and long gates run with `run_in_background: true` — a coordinator blocked
  on a gate or a whole-diff read is the wave's bottleneck. Throughput comes from turnover: an
  integrated story's files leave the collision set and unblock the next dispatch.
- **New §1.0 resume before you dispatch.** Requested in five sessions and previously covered
  nowhere. Unmerged `impl/*` branches and dirty implementor worktrees outrank fresh `ready` stories;
  a stale branch is brought current by merging `main` into it, never rebasing, because the
  implementor's history is the audit trail; resume worktrees go outside the harness-owned
  `.claude/worktrees/` namespace, which gets swept under a running agent; and a "completed" task
  notification does not mean the agent is finished — on resume its cwd falls back to the shared
  checkout on `main`.
- **Report ergonomics and closed verdict vocabularies.** Implementor report fields decayed down the
  page — `BRANCH:` 100%, `TEST:` 83%, `ACCEPTANCE:` 67%, `ADJACENT:` 57% — so the fields the
  coordinator most needs to review were the ones most often dropped. The four load-bearing fields
  now sit directly after identification, `GATE:` is capped at the tail of each command, and the
  enumerations move to the bottom. `story-impl` returns exactly `COMPLETE | PARTIAL | BLOCKED`;
  `story-review` returns exactly `PASS | REWORK | PARK` and the coordinator treats any other token
  as REWORK — 5 of 21 real reviews returned `APPROVE`, `CONCERNS` or `INTEGRATE`. `PARK` now has its
  trigger spelled out, distinct from `REWORK`, having never once been used in 21 reviews.

`skills/impl-coord/DESIGN.md` is revised rather than appended to, so the design record never states
two positions at once; its verification list now covers the new behaviours. Marketplace bumped to
0.8.0.

## [0.7.1] - 2026-07-29

### Fixed

#### Flux Agent Plugin (0.1.1)

- **Removed a stray `__pycache__/*.pyc` that shipped in 0.7.0.** Running the plugin's own offline
  tests before packaging left a compiled artifact in `scripts/`, which was then committed and
  distributed. Untracked it and added a Python section to `.gitignore` so it cannot recur.

## [0.7.0] - 2026-07-29

### Added

#### Flux Agent Plugin (0.1.0) — new

- **`flux-agent` — drive the flux agent as a sub-agent, over a protocol instead of prose.**
  Dispatching work to [flux](https://github.com/codewandler/flux) headlessly is currently
  untrustworthy in a specific, reproducible way: a turn that dies on a provider error exits **0**,
  emits no NDJSON `error` line, and reports the failure as prose inside an otherwise-normal
  `turn_end` (a stage `Err` is converted into an `Ok` value in `flux-flow`'s `detect_intent` /
  `explore`). A dropped provider stream additionally ends a long run outright, with no retry. The
  plugin encodes the workarounds so they are not rediscovered mid-task.
  - **`flux-agent` skill** — the three trust rules (never key on the exit code; never trust a clean
    `turn_end`; ground truth is a predicate you evaluate yourself), plus evidence-based model
    selection, task-prompt discipline, and worktree/disk isolation guidance for fan-out.
  - **`references/protocol.md`** — the observed `--stream-json` line vocabulary field by field,
    which fields are safe to key on, and a deterministic reproducer for the failure-looks-like-
    success gap.
  - **`scripts/flux_run.py`** — speaks NDJSON, classifies failures as transport (retryable) vs task
    (never retryable), resumes transport failures via `flux run --continue` with bounded backoff,
    **stops on a failure that repeats identically** rather than burning budget re-running a
    deterministic bug, and verifies completion against a `--success-cmd` ground-truth predicate that
    overrules any claim the model makes. Emits one JSON result; exits non-zero unless the predicate
    is satisfied.
  - **`scripts/test_flux_run.py`** — offline tests for the classifier. No network, key, or flux
    binary required.

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

[0.8.0]: https://github.com/codewandler/agentplugins/releases/tag/v0.8.0
[0.7.1]: https://github.com/codewandler/agentplugins/releases/tag/v0.7.1
[0.7.0]: https://github.com/codewandler/agentplugins/releases/tag/v0.7.0
[0.6.1]: https://github.com/codewandler/agentplugins/releases/tag/v0.6.1
[0.6.0]: https://github.com/codewandler/agentplugins/releases/tag/v0.6.0
[0.5.0]: https://github.com/codewandler/agentplugins/releases/tag/v0.5.0
[0.4.0]: https://github.com/codewandler/agentplugins/releases/tag/v0.4.0
[0.3.0]: https://github.com/codewandler/agentplugins/releases/tag/v0.3.0
[0.2.0]: https://github.com/codewandler/agentplugins/releases/tag/v0.2.0
[0.1.0]: https://github.com/codewandler/agentplugins/releases/tag/v0.1.0
