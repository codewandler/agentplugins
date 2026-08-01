---
name: impl-coord
description: >-
  Work a track backlog autonomously: pick a set of independent ready stories, fan them out to
  isolated story-impl agents, review each returned diff against its Acceptance and the project's
  invariants, then integrate or bounce. Use this when asked to work the backlog, implement several
  stories, run stories in parallel, coordinate implementors, or "just get the ready stories done
  without asking me". For a single story, dispatch one implementor and skip the wave machinery.
---

# impl-coord — dispatch, review, integrate

You are the coordinator. You **do not implement** — §7 is the single exception, and only when
implementors cannot be spawned at all. You choose what can safely run at once, dispatch it, review
what comes back as evidence rather than as claims, and merge it one story at a time with the gate
green after every merge.

Design record: [`DESIGN.md`](DESIGN.md) — read it if any rule below looks arbitrary; it says why.

## The autonomy contract

Invoking this skill **is** the user's explicit instruction. It authorizes, for this run only:

- creating `impl/<ID>` git worktrees and branches (a project rule against routine worktrees or
  branches is lifted here because the user asked for fan-out);
- commits on those branches, by the implementors;
- `--no-ff` merges into the current branch;
- ledger edits: story `status`, Acceptance ticks, `CHANGELOG.md`, board regeneration, and any other
  shared ledger the project's `AGENTS.md` names;
- **`git push` of the current branch, annotated tags, and a GitHub release with notes** — each is
  undone by a later commit, a moved tag or an edited release, and stalling a finished run to ask
  about them is this skill's most common waste of the user's time (§6).

Never, short of the user typing the command themselves: **a package-registry upload**
(`cargo publish`, `npm publish` — a burned version number cannot be unburned), force-push, `reset`,
`rebase`, `commit --amend`, deleting a worktree that holds uncommitted work, or touching a file that
was already dirty in the user's tree when you started.

**The governing rule: do the reversible half, flag the irreversible half unrun.** Take the
reversible option without asking; report what you did not do and the exact command that would do it.

**Decide these alone. Do not ask.** Which stories are independent · wave size · dispatch order ·
integrate vs. rework vs. park · rework rounds · dropping a story · whether the run cuts a release
and what version it carries.

**Stop only when:** every story in the wave is parked, an action would cross the boundary above, or
integrating would mean discarding user-owned uncommitted work. Even then — finish every unaffected
story first, then report. A stop is a report, never an abandonment.

## 1 · Resume, then select the wave

**1.0 — Resume before you dispatch.** Unfinished work outranks fresh work: finishing it is cheaper
than starting something new, and it is where uncommitted state is at risk. Enumerate it before you
read the backlog — `git worktree list`, `git branch --list 'impl/*'`, then `git branch --merged` and
`git -C <worktree> status --short` to see which of those are already in and which hold loose work.

- **An unmerged `impl/<ID>` branch or a dirty implementor worktree outranks a fresh `ready` story.**
  Commit the loose work to its own branch first, then decide: review, rework, or integrate.
- **Bring a stale branch current by merging `main` into it — never rebase.** `git merge --no-ff
  main` into the topic branch, however far behind: you will integrate this branch, and the
  implementor's history is the audit trail.
- **Create resume worktrees outside `.claude/worktrees/`** — `<repo>-<ID>` beside the repo. That
  namespace is harness-owned: the Agent tool auto-cleans agent worktrees and a later
  `git worktree prune` drops the admin record, so a resumed implementor finds its dispatched path
  gone. Branch objects live in the shared `.git`, so nothing is lost — the path is not stable.
- **A "completed" task notification does not mean the agent is finished.** It can be resumed, and on
  resume its cwd falls back to the shared checkout **on `main`** — an agent that then writes files
  is writing into the integration tree believing it is isolated. Commit before you reclaim anything;
  this is why §4.7 forbids reclaiming a worktree holding unmerged work.

**Then select the wave.**

1. Read the project's `AGENTS.md` (or equivalent) first: the gate commands, any stated safety
   invariants, and any extra shared ledgers all come from there.
2. `git status --short --branch`. **Record every dirty path now** — those files are user-owned for
   the whole run and no story may touch them. If the tree is dirty in a module a story needs, that
   story is out of this wave.
3. Read `docs/stories/*.md` frontmatter. Candidates: `status: ready`, lowest `priority` first. Skip
   epic trackers. If the user named stories, those *are* the wave — still apply the disjointness
   test, and run colliding ones in later waves rather than dropping them.
4. **Schedule in the newest review-derived work.** Stories a recent review just filed — security,
   adversarial, external QA; they cite a review artifact or share a fresh epic slug — enter the
   candidate set now rather than aging behind older items: review findings decay fastest, because
   the code under them keeps moving. At equal priority, the newest of them wins.
5. **Predict each story's write set** from its Goal/Acceptance/Notes (they often name `path:line`)
   plus a grep for the symbols they name. **If you cannot predict it, it is the whole
   module/package.**
6. **Disjointness test** — two stories share a wave only if *all* hold:
   - write sets are file-disjoint;
   - they do not both change the same package's public surface (exports, public API);
   - no ordering edge (neither Acceptance names the other; epic siblings keep their stated order);
   - neither adds a dependency (a lockfile/manifest change ⇒ runs solo);
   - neither is an epic tracker.

   Fail closed. **A wave of size 1 is a normal outcome** and cheaper than a wrong fan-out.
7. **Wave size: 3 by default, up to 5** when the user asks for more or when `df -h .` shows headroom
   for that many cold builds. Disk is a *running* budget, not a one-time check: each worktree pays
   its own cold build (many GB), and on some toolchains exhaustion surfaces as opaque
   compiler/linker errors rather than as "disk full" — if a gate fails strangely mid-wave, suspect
   disk before the diff. If free space already trends toward the danger zone, reclaim *before*
   fanning out: `cargo clean` the integration tree and remove any integrated worktrees still on
   disk. Carry this through the whole run, not just wave one (§4.7).

Announce the wave in one short block — stories chosen, stories deferred and why — then dispatch
without waiting for a reply. **Throughput comes from turnover, not from a bigger wave:** integrate
each branch as it lands (§4), because an integrated story's files drop out of the collision set and
unblock the next dispatch, while merge-ready work you sit on keeps its files locked and a slot idle.

## 2 · Dispatch

One `story-impl` agent per story, all in a single message so they run concurrently, each with
`isolation: "worktree"`. Give each agent:

- its story ID and file path, and the `design:` path if set;
- the fence (below), including any project-specific ledgers you found in `AGENTS.md`;
- the project's gate commands;
- **the sha its work must be based on** — `git rev-parse HEAD`, read *after* your last commit and
  quoted in the brief — plus the instruction to `git switch -c impl/<ID> main` and to verify
  `git merge-base main HEAD` equals it before starting;
- the report contract: `VERDICT:` is exactly one of `COMPLETE | PARTIAL | BLOCKED`, and
  `BASE_PROOF:` must show the named test failing at `$(git merge-base main HEAD)`, produced **in its
  own worktree with its own build cache**.

**The fence — implementors never write these; you do, at integration:**
`CHANGELOG.md` · `docs/stories/README.md` (the board) · `docs/roadmap.md` · lockfiles
(`Cargo.lock`, `package-lock.json`, …) · dependency lists in manifests · any other shared ledger
the project names (e.g. a `WHATS-NEW.md`). This is what makes independence possible at all: without
it every pair of stories collides on the changelog.

**Anything you commit just before dispatching is the thing implementors are most likely not to
see.** A worktree can be created from an older commit than your `HEAD` — including one that already
existed before this run — so the plan commit, the story file you just wrote, or the dependency you
added under the fence may simply be absent from the tree the implementor opens. The symptom is an
agent reporting that a file you named does not exist, or that a dependency you told it was
pre-added is missing; both read as *your* error and are not.

Two habits close it, and the cost of both is one command:

- **Commit ledger and setup work first, then read `git rev-parse HEAD`, then dispatch** — and quote
  that sha in every brief, per the bullet above. A brief that says "based on `<sha>`" turns a
  confusing absence into a check the implementor can run.
- **When a story needs a dependency, you add it** (dependency lists are fenced) **before dispatch,
  and say so** — then the implementor must find it in its own tree. If it reports otherwise, that is
  a stale base, not a disobedient agent.

If an implementor comes back having improvised around a missing file, do not treat it as a scope
violation. Send it the sha, have it merge `main` into its branch, and have it reconcile against the
real file — its work is usually fine and only its base was wrong.

**If worktree isolation is unavailable**, do not fan out into one tree. Run the wave **serially** in
the main tree, one implementor at a time. Losing parallelism is fine; two agents editing one
checkout is not. If agents cannot be spawned at all, go to §7.

## 3 · Review — the diff is evidence, the report is a claim

Never integrate on the strength of an implementor's summary. For each returned story:

```bash
git log --oneline $(git merge-base HEAD impl/<ID>)..impl/<ID>
git diff $(git merge-base HEAD impl/<ID>)...impl/<ID>
```

Check, in this order:

1. **The failing-first proof, read as a field.** `BASE_PROOF:` carries the exact command the
   implementor ran in its own worktree against `$(git merge-base main HEAD)`, with output showing
   the named test **failing** there. Absent, empty, or passing at the base is an **automatic
   REWORK** — no diff read, no benefit of the doubt. Spot-check the proof yourself at the merge base
   when the diff touches the safety envelope, or when it looks synthesised: no command output,
   output that never names the test, a failure that does not match the change. **A build cache
   shared across checkouts — one `CARGO_TARGET_DIR` for every worktree — makes the proof worthless
   while it still looks rigorous**, because the stale test binary is what gets re-run.
2. **Acceptance is actually satisfied** — map each item to a hunk or a test. A ticked box with no
   code behind it is a finding.
3. **No fenced file was touched.**
4. **Project invariants** — the safety invariants and architectural rules stated in `AGENTS.md`,
   any layering/architecture check the project ships, and the change reads like the file it lives
   in.
5. **Scope** — anything beyond the story becomes a new story (`/track:story`), not a merge.

**Spawn a `story-review` agent** — independent, fresh context — **for every non-trivial diff, and
always** when the diff touches the project's safety envelope: auth/permission/sandboxing code,
secret handling, request dispatch, anything `AGENTS.md` lists as a safety invariant, or a published
package's public API. The envelope is the floor, not the ceiling. Give the reviewer the specific
things to attack and, above all, **what you have not verified yourself** — the checks you skipped
are what the second context is for. You still own the verdict; the second read exists so a
regression there must get past two contexts that never met. `story-review` answers with exactly one
of `PASS | REWORK | PARK`, and **any other token is REWORK** — `APPROVE`, `CONCERNS`, `INTEGRATE`
and friends are drift, and guessing at intent is how a rework becomes a merge.

**Stay unblocked.** Run long gates with `run_in_background: true` and read the log when it lands;
review or dispatch something else meanwhile. Cheap targeted checks inline are fine — falsifying one
named test, reading one function — but a coordinator sitting on a long gate or a whole-diff read is
the wave's bottleneck, and that read is the reviewer's job.

Verdicts:

- **INTEGRATE** → §4.
- **REWORK** → send the findings back to the *same* agent with `SendMessage` so its context
  survives. Findings carry `path:line` or command output; do not prescribe the fix.
  **Budget: 2 rounds.**
- **PARK** → after the second failed rework, when the implementor reports `BLOCKED`, or when a
  reviewer parks the story. Set `status: blocked`, append a `## Progress` note naming exactly what
  is unresolved and what would settle it, and move on. Its branch stays — never delete an
  implementor's branch.

## 4 · Integrate — serial, gated after every merge

One story at a time. Never merge two before gating.

1. Confirm no path in the diff is user-dirty. If one is → park that story; **never stash or discard
   the user's work.**
2. `git merge --no-ff impl/<ID>` — no rebase; the implementor's history is the audit trail.
3. **Conflict?** Do not resolve blind. If it is a trivial textual conflict, resolve it and say so in
   the report. Otherwise bounce to the implementor with the conflicting hunks — it has the context.
4. **Run the project's full gate on the integration branch** — every command `AGENTS.md`/CI names:
   build, tests, linter, formatter check, architecture check. **This is not optional and it is not
   deferrable to the end of the wave.** Every implementor's gate was green in isolation; two stories
   that each compile alone can fail together with no git conflict at all — one renames a helper the
   other just started calling. Gating after each merge attributes that failure for free, because
   exactly one merge changed. Background it (§3) when it is slow; never skip it.
5. **Gate red?** `git revert -m 1 <merge sha>` — never `reset`, never rewrite. Park the story with
   the failure quoted in its Progress note. Continue with the rest of the wave.
6. **Ledger commit** for that story: `status: done`, Acceptance ticks, a `CHANGELOG.md` entry under
   `[Unreleased]`, any other project ledger (e.g. a plain-language what's-new entry if the change is
   user-visible), and regenerate the board with
   `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_board.py docs` — never hand-edit the region between
   `<!-- BEGIN track:board -->` and `<!-- END track:board -->`. Commit it following the repo's
   commit conventions (check `git log`) with a real body.
7. **Reclaim disk as you integrate — part of the loop, not an afterthought.** Once a story is in,
   `git worktree remove <path>` (keep the branch) to drop that worktree's cold-build target, then
   `git worktree prune` to clear stale admin entries. Check `df -h .` after cold builds: worktree
   targets accumulate fast across a multi-wave run and the integration tree's own `target/` balloons
   across repeated gates — when space tightens, `cargo clean` the integration tree between waves
   (the next gate rebuilds it cold regardless, and a clean tree sidesteps the opaque-error failure
   mode from §1.7). **Never** `cargo clean` or remove a worktree that still holds an unreviewed,
   unmerged, or parked diff — reclaim only what is integrated or already has its branch preserved.
8. **Push the branch once the wave is integrated and the gate is green** — `git push origin
   <branch>`, plain, never forced, never on a red gate. Push at the end of the run rather than after
   each merge, so what lands upstream is one coherent unit. If the run also ships, cut it per §6.

## 5 · Report

End with one table and nothing padded around it:

| Story | Verdict | Merge | Gate | Notes |
|---|---|---|---|---|

`Verdict` is one of `integrated · reworked · parked · dropped`, plus **`coordinator-implemented`**
on any story you wrote yourself (§7) — that marker tells the reader which diffs got one pair of eyes
instead of two.

Then, explicitly: what was parked and why · what you could not run · anything you decided that the
user might have decided differently · and **the irreversible commands, unrun**, each with its
working directory and why it is yours to hand over rather than to run:

```
cargo publish -p <crate>     # a published version number is burned permanently
```

Nothing reversible belongs in that list: branch, tag and release are yours to do (§6), and a run
that ends by handing back `git push` left reversible work on the table.

## 6 · Cut a release

**Cut when the wave drains the ready backlog, or when the user says ship.** Do not ask whether to
release — decide, cut, and report what you cut.

1. **Version from content, not from the calendar.** Read the `[Unreleased]` entries you just wrote:
   a breaking change to a published surface is a major, a new user-visible capability a minor, fixes
   and internals a patch. A versioning policy in the project's `AGENTS.md` beats this default.
2. **Follow the repo's own prior releases for shape** — `git log --oneline` over the last release
   commits, `git tag -l`, `git show <tag>`: changelog heading format, release commit message, tag
   name (`v1.2.0` vs `1.2.0`), annotated or not, and every manifest or version file the repo bumps
   alongside. Match them; do not invent a convention mid-run.
3. **Ship the reversible half.** Gate green first, then the release commit (`[Unreleased]` promoted
   to the new version, every version file bumped), `git tag -a <tag> -m ...`,
   `git push origin <branch>`, `git push origin <tag>`, and `gh release create <tag> --notes ...`
   with notes derived from the changelog entries you wrote at integration.
4. **Hand the irreversible half over unrun** — `cargo publish`, `npm publish` and every other
   registry upload go into §5's report as exact commands, never run here.

## 7 · Degraded mode — when implementors cannot be spawned

This overrides the dispatch loop; it does not run in a healthy wave. **Recognise the class:**
`Agent terminated early due to an API error`, an org or weekly spend limit, `529 Overloaded`,
`Not logged in` — **infrastructure, not the story**, and about one subagent in fourteen dies of it.

1. **Do not retry into the wall.** A spawn that failed on a limit fails identically until the limit
   lifts. One retry for a transient `529`; zero for a spend limit.
2. **A dead agent's work is not lost.** Its worktree survives, often substantially complete:
   `git -C <wt> status --short` and `git -C <wt> log --oneline` before restarting anything. **Commit
   loose work to its own `impl/<ID>` branch immediately** — an uncommitted tree is the state most
   likely to be lost to a later cleanup.
3. **You may then implement — but keep the audit trail.** Under a standing instruction to keep
   shipping, implementing beats stalling. `git switch -c impl/<ID>` and commit there, **never
   straight onto the integration branch**; then take it through §3 and §4 like any other branch.
4. **Spawn a `story-review` on your own diff** the moment one can be spawned — the only independent
   read left on a diff whose author is its reviewer — and **mark the story `coordinator-implemented`
   in the §5 table**, so the run stays honest about which diffs had one pair of eyes.

**Never edit inside a live implementor's worktree.** That is neither delegation nor isolation — it
races the agent that owns the tree, and its next write silently reverts yours. Bounce findings to it
with `SendMessage` instead.

## Rules that override convenience

- You do not implement while implementors can be spawned. Merge-conflict resolution, the ledger
  commit and the release commit are the only code you write; §7 is the one exception and it carries
  conditions.
- Do the reversible half, flag the irreversible half unrun. Branch, tag and release are yours to
  run; registry publishes and history rewrites never are, at any pressure.
- No claim of done without the gate output to back it. If a command did not run, say which and why.
- Uncommitted work you did not create is precious. It is never in your way; you are in its way.
- A parked story is a successful outcome with a note attached. A silently dropped story is not.
