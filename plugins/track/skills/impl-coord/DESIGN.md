# Implementation coordinator — autonomous fan-out over independent stories

Status: design · Artifacts: `skills/impl-coord/SKILL.md`, `agents/story-impl.md`,
`agents/story-review.md`

## The problem

The board is a queue of independently-specified units of work. Working it one story at a time in one
session has two costs that compound:

1. **Serialization.** Stories that share no file wait on each other for no reason.
2. **Question latency.** A single session that hits an ambiguity stops the *whole* queue to ask,
   even when four other ready stories were untouched by that ambiguity.

The second cost is the one that actually hurts. Asking is cheap for the agent and expensive for the
user, so the default drifts toward asking — and the queue stalls on the slowest human reply rather
than on the hardest problem.

## The shape

Three pieces, and the split between them is the design:

| Piece | Kind | Runs in | Holds |
|---|---|---|---|
| `impl-coord` | skill | the main session | dispatch, review, **merge authority**, the report |
| `story-impl` | agent | its own git worktree | one story, end to end, on a scratch branch |
| `story-review` | agent | fresh context, read-only | an independent verdict on a risky diff |

**The coordinator is a skill, not an agent**, because it holds merge authority and must stay
directly interruptible by the user. Nesting it one level down would make every stop condition a
relayed message and put the wave report behind a summarizer.

**The coordinator never implements.** If it starts fixing the diffs it dispatched, it is reviewing
its own work and the wave's audit trail collapses to "one session did everything, in parallel". Two
exceptions, both mechanical: resolving a textual merge conflict, and writing the ledger commit.

## Autonomy is a contract, not a vibe

Autonomy that isn't bounded is just an agent that doesn't ask before doing the irreversible thing.
So the boundary is explicit and it is the same boundary in all three artifacts.

**Invoking `impl-coord` is the standing authorization for:** creating `impl/<ID>` branches and
worktrees; commits on those branches; `--no-ff` merges into the current branch; and the ledger edits
(story status, Acceptance ticks, CHANGELOG, board regeneration, other project-named ledgers).

This is a deliberate, scoped lift of standing rules like "never commit without explicit
instruction" or a project's "don't create branches or worktrees as a matter of course". Fan-out
*is* the explicit instruction: work in N isolated trees cannot be integrated without commits, and a
coordinator that leaves N dirty worktrees for the user to reconcile by hand has done the hard part
and skipped the useful part.

**It is never authorization for:** `git push`, tags, a release or publish, any history rewrite
(`reset`, `rebase`, `commit --amend`, force-push), deleting a worktree with uncommitted work in it,
or touching a file that was already dirty in the user's tree when the wave started.

**Decided alone, no question asked:** which stories are independent, dispatch order, wave size,
integrate vs. rework vs. park, how many rework rounds a story gets, and dropping a story from the
wave.

**Stop conditions — the complete list:** every story in the wave is parked; an action would cross
the boundary above; or integration would require discarding user-owned uncommitted work. Even then,
the rule is *finish everything unaffected first, then report* — a stop is a report, not an
abandonment.

## Wave selection favors fresh review output

Candidate order is `status: ready` by `priority` — with one deliberate bias: stories and epics just
filed out of a review process (security review, adversarial review, external QA) are scheduled into
the earliest possible wave. Review findings are pinned to the state of the tree the reviewer saw;
every unrelated merge after that erodes their `path:line` evidence and widens the re-verification
cost. Older backlog stories don't decay that way. So at equal priority, review-derived work goes
first.

## Independence: the disjointness test

A wave is only as good as its independence test, and the naive test ("different stories") is wrong
for a specific reason: **every story touches `CHANGELOG.md` and the board.** Under a file-overlap
rule, no two stories are ever independent.

So the first structural decision is to remove that class entirely:

> **Implementors do not write the shared ledgers.** They write code, tests, their own
> `docs/stories/<ID>-*.md`, and their own design doc. `CHANGELOG.md`, `docs/stories/README.md`,
> `docs/roadmap.md`, lockfiles, and any other project-named ledger are **fenced** — the coordinator
> writes them, once, at integration.

With the fence in place, two stories may share a wave iff **all** hold:

1. **Predicted write sets are file-disjoint.** Predicted from the story's Goal/Acceptance/Notes
   (which routinely name `path:line`) plus a grep for the symbols they name. *If the write set
   cannot be predicted, it is the whole module/package* — conservative by default.
2. **No shared public surface.** Two stories may both edit a package's internals; they may not both
   edit its exports.
3. **No ordering edge.** Neither Acceptance names the other, and epic siblings keep their stated
   order.
4. **Neither is an epic tracker.** Epics are narratives, not work.
5. **Neither adds a dependency.** A lockfile/manifest change runs solo.

A wave of size 1 is a normal, correct outcome. Fanning out two stories that turn out to collide
costs more than running them in sequence, so the test fails closed.

## Isolation, and what it costs

Each implementor gets its own git worktree and creates `impl/<ID>` inside it before its first
commit. Work is located **by branch ref, not by path** — refs live in the shared `.git`, so the
coordinator can read, diff, and merge an implementor's work whether or not the worktree still
exists.

The cost is real and worth stating: separate worktrees mean separate build directories, so each
implementor pays a cold build. On some toolchains disk exhaustion surfaces as opaque
compiler/linker errors rather than as "disk full". Mitigations, in the skill: **cap the wave at
3**, check free disk before dispatch, and remove each worktree after its story integrates. A shared
build cache is *not* the fix where fingerprints are path-dependent — the implementors would
invalidate each other's artifacts continuously.

If worktree isolation is unavailable, the fallback is a **serial wave in the main tree** — one
implementor at a time. Losing parallelism is acceptable; letting two agents edit one tree is not.

## Review: the diff is the evidence, the report is a claim

The coordinator reviews the **diff**, never the implementor's summary. Prose is a claim to be
tested; the tree is evidence.

One check earns its place above the rest: **re-run the named failing-first test against the merge
base.** "I wrote a failing-first test" is the single most load-bearing and least verifiable claim in
an implementor's report, and confirming it costs one command. A test that passes on the base proves
the change is unpinned.

The rest of the checklist is the project's own invariant list (`AGENTS.md`), any
layering/architecture check it ships, fenced-file edits, and scope creep.

An **independent** `story-review` agent is spawned — fresh context, read-only — when the diff
touches the safety envelope: auth/permission/sandboxing code, secret handling, request dispatch,
anything the project lists as a safety invariant, or a published package's public API. The
coordinator still owns the verdict; the second read exists so a subtle envelope regression has to
get past two contexts that never saw each other's reasoning.

Verdicts: **INTEGRATE**, **REWORK** (specific, evidence-anchored reasons, sent back to the *same*
agent so its context survives), **PARK**. The rework budget is 2 rounds; the third failure parks the
story as `blocked` with a Progress note naming exactly what is unresolved, and the wave continues.

## Integration: serial, gated after every merge

Merges happen one at a time, and the gate runs **after each one**, on the integration branch — not
once at the end.

This is the part that cannot be skipped. Every implementor's gate was green *in isolation*. Two
stories that each compile alone can fail together: one renames a helper the other started calling,
one tightens a type the other widened. Git reports no conflict because the hunks don't overlap. A
single gate run at the end of the wave finds the failure but cannot attribute it; a gate run after
each merge attributes it for free, because exactly one merge changed.

On red: `git revert -m 1` the offending merge — never a reset, never a history rewrite — park the
story, continue with the rest.

Then, per story, one ledger commit: `status: done`, Acceptance ticks, the CHANGELOG entry, any
other project ledger, and one board regeneration. Nothing is pushed. The wave report ends with the
push command for the user to run.

## What this does not do

- **It does not make dependent work parallel.** It makes independent work concurrent, and it is
  conservative about which is which.
- **It does not replace a project's release gates.** Whatever end-to-end or live smoke checks the
  project requires before release still run there.
- **It does not judge product fit.** Acceptance is the contract. A story whose Acceptance is wrong
  produces a correctly-implemented wrong thing, and that is a backlog problem, not a wave problem.
- **It does not detect semantic conflicts before merging.** The post-merge gate is the net, and the
  cost of that net is a full gate run per merge.

## Verification

- A two-story wave over stories in different packages integrates both, with a gate run recorded
  after each merge.
- A wave whose second merge breaks the gate reverts exactly that merge and reports the first story
  as integrated.
- An implementor that edits a fenced file is bounced, not integrated.
- An implementor whose failing-first test passes on the merge base is bounced.
- Nothing in a wave produces a `git push`, a tag, or a rewritten history.
