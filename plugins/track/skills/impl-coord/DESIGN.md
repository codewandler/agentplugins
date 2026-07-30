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
| `story-review` | agent | fresh context, read-only | an independent verdict on a returned diff |

**The coordinator is a skill, not an agent**, because it holds merge authority and must stay
directly interruptible by the user. Nesting it one level down would make every stop condition a
relayed message and put the wave report behind a summarizer.

**The coordinator does not implement.** If it starts fixing the diffs it dispatched, it is reviewing
its own work and the wave's audit trail collapses to "one session did everything, in parallel". Two
mechanical exceptions: resolving a textual merge conflict, and writing the ledger commit. One
non-mechanical exception exists and is specified rather than improvised — see *Degraded mode*.

## Autonomy is a contract, and the line is reversibility

Autonomy that isn't bounded is just an agent that doesn't ask before doing the irreversible thing,
so the boundary is explicit and it is the same boundary in all three artifacts. The first version
drew it at *effects that leave the local tree*: push, tags and releases were never authorized.
Eighteen measured runs say that was the wrong place. Users granted the pushing half in nine of them,
usually bluntly (*"just push it yourself and create a release in gh with release notes"*), and most
of the twenty-five questions the coordinator asked were release-scope questions. That is the failure
chain this design exists to eliminate: **a forbidden action with no guidance turns into a question,
and a question stalls the queue on a human reply.** Forbidding what the user keeps granting buys
latency, not safety, and it trains the coordinator to ask — the habit the whole skill is built
against.

Reversibility is what actually separates the two halves. A pushed branch can be updated, a tag
moved, a release deleted; the repository owner keeps every remedy. A burned version number cannot be
unpublished, and a rewritten history cannot be recovered from the tree that overwrote it. **The
governing rule: do the reversible half, flag the irreversible half unrun** — take the reversible
option without asking, and report what was not done with the exact command that does it.

| Reversible — `impl-coord` authorizes it | Irreversible — never authorized, flagged unrun |
|---|---|
| `impl/<ID>` branches, worktrees, their commits | a package-registry upload |
| `--no-ff` merges into the current branch | history rewrite: `reset`, `rebase`, force-push |
| ledger edits: status, ticks, CHANGELOG, board | deleting a worktree with uncommitted work |
| `git push` of the branch, tags, a GitHub release | touching a file the user left dirty |

The left column is a deliberate, scoped lift of standing rules like "never commit without explicit
instruction": work in N isolated trees cannot be integrated without commits, and a coordinator that
leaves N dirty worktrees to reconcile by hand has done the hard part and skipped the useful part.
The right column is short on purpose — `cargo publish`/`npm publish` burn a version number, and
`commit --amend` on a branch under review destroys the audit trail. And because release scope was
the largest single source of questions, the skill's *Cut a release* section makes it a decision
rather than a question: cut when the wave drains the ready backlog or the user says ship, version
from content not the calendar, take the shape from the repo's own prior release commits and tags.

**Decided alone, no question asked:** which stories are independent, dispatch order, wave size,
integrate vs. rework vs. park, how many rework rounds a story gets, dropping a story from the wave,
and whether the wave ends in a release.

**Stop conditions — the complete list:** every story in the wave is parked; an action would cross
the irreversible boundary above; or integration would require discarding user-owned uncommitted
work. Even then, the rule is *finish everything unaffected first, then report* — a stop is a report,
not an abandonment.

## Resume before you dispatch

Five sessions opened with a variant of *"check stale worktrees for pending work, bring it to life
again"* and the skill had nothing to say about it; the knowledge lived only in per-project memory.
So resuming outranks starting: **an unmerged `impl/<ID>` branch or a dirty implementor worktree is
picked up before a fresh `ready` story.** Finishing started work is cheaper than starting it, and it
is the one place in the system where uncommitted state sits at risk.

**Merge `main` in, never rebase.** The reason the contract forbids history rewrite is specific here:
the implementor's commit sequence *is* the audit trail for a diff the coordinator did not write, so
`git merge --no-ff main` is the move even when the branch is far behind.

**Resume worktrees live outside `.claude/worktrees/`.** That namespace is harness-owned — the Agent
tool auto-cleans agent worktrees and a later `git worktree prune` drops the admin record, so a
resumed implementor finds its dispatched path gone. Branch objects live in the shared `.git`, so
nothing is lost, but the *path* is not stable. The sharper corollary: a "completed" notification
does not mean the agent is finished, and a resumed agent's cwd falls back to the shared checkout on
`main`, where it writes into the integration tree believing it is isolated. Hence
commit-before-reclaim, and hence no reclaiming a worktree that still holds unmerged work.

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
rule, no two stories are ever independent, so the first structural decision removes that class
entirely:

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
exists. The cost is real: separate worktrees mean separate build directories, so each implementor
pays a cold build, and on some toolchains disk exhaustion surfaces as opaque compiler/linker errors
rather than as "disk full". A shared build cache is *not* the fix where fingerprints are
path-dependent — implementors would invalidate each other's artifacts continuously, and a shared
target directory also destroys the merge-base proof described below.

The original mitigation was a flat cap of three implementors per wave, calibrated against **disk
alone** and then read as a policy limit. Five of eighteen sessions exceeded it anyway (waves of 4, 5
and 7) and four sessions had the user ask for five outright. Disk is a budget, not a constant, so
the cap is stated as one: **three by default, up to five when the user asks or when `df` shows
headroom for that many cold builds.** The disjointness test above is untouched — the budget says how
many independent stories may run, never which stories count as independent. The other mitigations
stand: check free disk before dispatch, remove each worktree once its story integrates, and where
worktree isolation is unavailable entirely fall back to a **serial wave in the main tree** — losing
parallelism is acceptable, letting two agents edit one tree is not.

The dial that actually moves throughput is not the cap. It is **integrating finished branches
promptly, so their files leave the in-flight write set and the next story becomes dispatchable.**
Sitting on merge-ready work while agents idle costs more parallelism than a wave slot does.

## Review: the diff is the evidence, the report is a claim

The coordinator reviews the **diff**, never the implementor's summary: prose is a claim to be
tested, the tree is evidence. One check earns its place above the rest — the named failing-first
test must **fail at the merge base**, because "I wrote a failing-first test" is the most
load-bearing and least verifiable claim in a report, and a test that passes on the base proves the
change is unpinned. Written as a coordinator procedure, that check ran **5 times in 169 dispatches
(~3%), and fourteen of eighteen sessions never ran it once** — while the fence, of comparable
importance in the same document with the same emphasis, held at **169/169**. The difference is not
attention, it is form: the fence is an enumerable list copied verbatim into every dispatch, so
producing the dispatch *is* producing the fence, whereas the merge-base check had to be remembered
afterwards against everything else in a long session.

**A rule that must be remembered as a procedure decays; a rule that becomes a required artifact
survives.** So the proof moves to the party already at the keyboard: `story-impl` emits a required
`BASE_PROOF:` field — the exact command, run in its own worktree against
`$(git merge-base main HEAD)`, with output showing the named test failing. The coordinator verifies
a *field*, which it cannot skip without noticing, instead of recalling a *step*, which it
demonstrably can; a proof that is missing, empty, or passing at the base is an automatic REWORK. The
expensive re-run becomes **targeted** rather than nominally universal — spot-checked when the diff
touches the safety envelope or when the proof looks synthesised, because a targeted check that runs
beats a universal one that does not.

The proof has one way to look rigorous and be worthless: a **build cache shared across checkouts**
(a shared `CARGO_TARGET_DIR` or equivalent) can re-run a stale binary, so its failure at the base
says nothing about the base. Hence the proof must come from the implementor's own worktree with its
own target directory, and hence the caveat is stated in `story-impl.md` and `story-review.md` both —
whoever reads a proof has to know how it can lie. The rest of the checklist is the project's own
invariant list (`AGENTS.md`), any layering/architecture check it ships, fenced files, and scope
creep.

**Independent review is a floor, not a ceiling.** The first version spawned `story-review` only for
the safety envelope: 42 spawns across 169 dispatches, four sessions spawning none, and a user asking
mid-run *"why are you reviewing this yourself and not using a review agent for it? you must remain
unblocked!"* That is a throughput complaint, not a quality one — a coordinator reading whole diffs
inline is a serialised pipeline with N idle agents attached. So a reviewer is spawned for **every
non-trivial diff** and **always** for the envelope, and the dispatch tells it **what the coordinator
has not verified itself**: the most useful thing to point a fresh context at, and an honest account
of the coverage. Long gates run backgrounded on the same logic; cheap targeted checks inline stay
fine, because the rule is about long gates and whole-diff reads, not about never running a command.

The coordinator still owns the decision — integrate, rework, or park. `story-review` returns a
verdict from a closed set (`PASS | REWORK | PARK`) and any other token is handled as REWORK: five of
twenty-one real reviews returned `APPROVE`, `CONCERNS` or `INTEGRATE`, and guessing at intent is a
worse failure than one round trip. Rework findings go back to the *same* agent so its context
survives. The budget is 2 rounds; the third failure parks the story as `blocked` with a Progress
note naming exactly what is unresolved, and the wave continues.

## Integration: serial, gated after every merge

Merges happen one at a time, and the gate runs **after each one**, on the integration branch — not
once at the end. This is the part that cannot be skipped. Every implementor's gate was green *in
isolation*, and two stories that each compile alone can fail together: one renames a helper the
other started calling, one tightens a type the other widened. Git reports no conflict because the
hunks don't overlap. A single gate run at the end of the wave finds the failure but cannot attribute
it; a gate run after each merge attributes it for free, because exactly one merge changed. Observed
adherence is 81% (179/221), high enough to keep mandatory and too low to relax; backgrounding the
gate is how it stops serialising the wave.

On red: `git revert -m 1` the offending merge — never a reset, never a history rewrite — park the
story, continue with the rest. Then, per story, one ledger commit: `status: done`, Acceptance ticks,
the CHANGELOG entry, any other project ledger, and one board regeneration. The branch and any tag
are pushed under the reversibility rule; registry publishes are handed over unrun, with the command.

## Degraded mode: when implementors cannot be spawned

**63 of 887 subagents (~7%) died to infrastructure rather than to code** — org spend limit, weekly
limit, `529 Overloaded`, `Not logged in`. The design had no answer for that state, because "the
coordinator never implements" quietly assumed implementors *exist*. Give a model a standing
instruction to keep shipping and no way to delegate, and it invents a fallback: one run logged
*"seven attempts, zero survivors ... so I stopped re-dispatching into a wall and did the work
myself"*, a defensible call that nevertheless dropped the branch, the isolation and the independent
review in one step, and another had the coordinator edit files inside a **live** implementor's
worktree — 15 edits, 7 files, racing the agent that owned the tree. The lesson is not that the
fallback was wrong; it is that an unspecified fallback discards whatever the spec did not name. So
degraded mode is specified, and what it preserves is the audit trail:

- **Recognise the class.** These are infrastructure errors, not the story, and a spawn that failed
  for a limit fails identically until the limit lifts. Re-dispatch is not a strategy.
- **A dead agent's work is not lost.** Its worktree survives, often substantially complete, so it is
  inspected and committed to its own `impl/<ID>` branch before anything restarts — an uncommitted
  tree is the state most likely to be swept by a later cleanup.
- **The coordinator may implement, on a branch.** `impl/<ID>`, never straight onto the integration
  branch, so the diff stays reviewable as a unit and revertable as one merge.
- **Independent review is the last thing to give up** — if a `story-review` can be spawned at all it
  is spawned on the coordinator's own diff, the only outside read left.
- **The report says so** — the story is marked `coordinator-implemented`, because a run that
  silently mixes two-eyes and one-eye diffs is lying about its own coverage.
- **Never edit inside a live implementor's worktree.** That is neither delegation nor isolation; it
  races the tree's owner. Findings go back by message.

## What this does not do

- **It does not make dependent work parallel.** It makes independent work concurrent, and it is
  conservative about which is which.
- **It does not replace a project's release gates.** Whatever end-to-end or live smoke checks the
  project requires before release still run there.
- **It does not judge product fit.** Acceptance is the contract. A story whose Acceptance is wrong
  produces a correctly-implemented wrong thing, and that is a backlog problem, not a wave problem.
- **It does not detect semantic conflicts before merging.** The post-merge gate is the net, and the
  cost of that net is a full gate run per merge.
- **It does not make a degraded-mode diff as trustworthy as a delegated one.** It keeps the branch,
  the review where possible, and an honest label — it does not restore the second pair of eyes.

## Verification

- A two-story wave over stories in different packages integrates both, with a gate run recorded
  after each merge; a wave whose second merge breaks the gate reverts exactly that merge and reports
  the first story as integrated.
- An implementor that edits a fenced file is bounced, not integrated.
- A report with `BASE_PROOF:` missing, empty, or showing the test passing at the merge base is
  bounced without further review.
- A `story-review` verdict outside `PASS | REWORK | PARK` is handled as REWORK, not interpreted.
- A wave over the disk budget is not dispatched; a wave of 4 or 5 goes out only on an explicit ask
  or measured headroom.
- A story the coordinator implemented under degraded mode lands on `impl/<ID>` and is marked
  `coordinator-implemented` in the report.
- A stale `impl/<ID>` branch is brought current by merging `main` into it, never by rebasing, and
  its resume worktree is created outside `.claude/worktrees/`.
- A release pushes the branch, the tag and a GitHub release, and hands over the registry publish
  unrun with the exact command.
- Nothing in a wave produces a force-push, a `reset`, or a rewritten history.
