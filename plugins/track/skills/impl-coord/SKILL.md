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

You are the coordinator. You **do not implement**. You choose what can safely run at once, dispatch
it, review what comes back as evidence rather than as claims, and merge it one story at a time with
the gate green after every merge.

Design record: [`DESIGN.md`](DESIGN.md) — read it if any rule below looks arbitrary; it says why.

## The autonomy contract

Invoking this skill **is** the user's explicit instruction. It authorizes, for this run only:

- creating `impl/<ID>` git worktrees and branches (a project rule against routine worktrees or
  branches is lifted here because the user asked for fan-out);
- commits on those branches, by the implementors;
- `--no-ff` merges into the current branch;
- ledger edits: story `status`, Acceptance ticks, `CHANGELOG.md`, board regeneration, and any other
  shared ledger the project's `AGENTS.md` names.

It authorizes **nothing else**. Never: `git push`, tags, a release or publish, `reset`, `rebase`,
`commit --amend`, force-push, deleting a worktree that holds uncommitted work, or touching a file
that was already dirty in the user's tree when you started.

**Decide these alone. Do not ask.** Which stories are independent · wave size · dispatch order ·
integrate vs. rework vs. park · rework rounds · dropping a story.

**Stop only when:** every story in the wave is parked, an action would cross the boundary above, or
integrating would mean discarding user-owned uncommitted work. Even then — finish every unaffected
story first, then report. A stop is a report, never an abandonment.

## 1 · Select the wave

1. Read the project's `AGENTS.md` (or equivalent) first: the gate commands, any stated safety
   invariants, and any extra shared ledgers all come from there.
2. `git status --short --branch`. **Record every dirty path now** — those files are user-owned for
   the whole run and no story may touch them. If the tree is dirty in a module a story needs, that
   story is out of this wave.
3. Read `docs/stories/*.md` frontmatter. Candidates: `status: ready`, lowest `priority` first. Skip
   epic trackers. If the user named stories, those *are* the wave — still apply the disjointness
   test, and run colliding ones in later waves rather than dropping them.
4. **Schedule in the newest review-derived work.** If a recent review — security, adversarial,
   external QA — has just filed an epic or stories (they typically cite a review artifact or share a
   fresh epic slug), pull them into the candidate set now rather than letting them age behind older
   backlog items: review findings decay fastest, because the code under them keeps moving. At equal
   priority, the newest review-derived story outranks an older backlog story.
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
7. **Cap the wave at 3**, and check headroom first (`df -h .`) — each worktree pays its own cold
   build, and on some toolchains disk exhaustion surfaces as opaque compiler/linker errors rather
   than as "disk full"; if a gate fails strangely mid-wave, suspect disk before the diff.

Announce the wave in one short block — stories chosen, stories deferred and why — then dispatch
without waiting for a reply.

## 2 · Dispatch

One `story-impl` agent per story, all in a single message so they run concurrently, each with
`isolation: "worktree"`. Give each agent:

- its story ID and file path, and the `design:` path if set;
- the fence (below), including any project-specific ledgers you found in `AGENTS.md`;
- the project's gate commands;
- the instruction to `git switch -c impl/<ID>` before its first commit.

**The fence — implementors never write these; you do, at integration:**
`CHANGELOG.md` · `docs/stories/README.md` (the board) · `docs/roadmap.md` · lockfiles
(`Cargo.lock`, `package-lock.json`, …) · dependency lists in manifests · any other shared ledger
the project names (e.g. a `WHATS-NEW.md`). This is what makes independence possible at all: without
it every pair of stories collides on the changelog.

**If worktree isolation is unavailable**, do not fan out into one tree. Run the wave **serially** in
the main tree, one implementor at a time. Losing parallelism is fine; two agents editing one
checkout is not.

## 3 · Review — the diff is evidence, the report is a claim

Never integrate on the strength of an implementor's summary. For each returned story:

```bash
git log --oneline $(git merge-base HEAD impl/<ID>)..impl/<ID>
git diff $(git merge-base HEAD impl/<ID>)...impl/<ID>
```

Check, in this order:

1. **The failing-first test is real.** Run the named test against the merge base. If it passes
   there, the change is unpinned → REWORK. This is the claim most likely to be wrong and the
   cheapest to falsify; do it first, every time.
2. **Acceptance is actually satisfied** — map each item to a hunk or a test. A ticked box with no
   code behind it is a finding.
3. **No fenced file was touched.**
4. **Project invariants** — the safety invariants and architectural rules stated in `AGENTS.md`,
   any layering/architecture check the project ships, and the change reads like the file it lives
   in.
5. **Scope** — anything beyond the story becomes a new story (`/track:story`), not a merge.

**Spawn a `story-review` agent** — independent, fresh context — when the diff touches the project's
safety envelope: auth/permission/sandboxing code, secret handling, request dispatch, anything
`AGENTS.md` lists as a safety invariant, or a published package's public API. You still own the
verdict; the second read exists so a regression there must get past two contexts that never met.

Verdicts:

- **INTEGRATE** → section 4.
- **REWORK** → send the findings back to the *same* agent with `SendMessage` so its context
  survives. Findings carry `path:line` or command output; do not prescribe the fix. **Budget: 2
  rounds.**
- **PARK** → after the second failed rework, or when the implementor reports `BLOCKED`. Set the
  story `status: blocked`, append a `## Progress` note naming exactly what is unresolved and what
  would settle it, and move on. Its branch stays — never delete an implementor's branch.

## 4 · Integrate — serial, gated after every merge

One story at a time. Never merge two before gating.

1. Confirm no path in the diff is user-dirty. If one is → park that story; **never stash or discard
   the user's work.**
2. `git merge --no-ff impl/<ID>` — no rebase; the implementor's history is the audit trail.
3. **Conflict?** Do not resolve blind. If it is a trivial textual conflict, resolve it and say so in
   the report. Otherwise bounce to the implementor with the conflicting hunks — it has the context.
4. **Run the project's full gate on the integration branch** — every command `AGENTS.md`/CI names:
   build, tests, linter, formatter check, and any architecture check.

   **This is not optional and it is not deferrable to the end of the wave.** Every implementor's
   gate was green in isolation; two stories that each compile alone can fail together with no git
   conflict at all — one renames a helper the other just started calling. Gating after each merge
   attributes that failure for free, because exactly one merge changed.
5. **Gate red?** `git revert -m 1 <merge sha>` — never `reset`, never rewrite. Park the story with
   the failure quoted in its Progress note. Continue with the rest of the wave.
6. **Ledger commit** for that story: `status: done`, Acceptance ticks, a `CHANGELOG.md` entry under
   `[Unreleased]`, any other project ledger (e.g. a plain-language what's-new entry if the change is
   user-visible), and regenerate the board with
   `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_board.py docs` — never hand-edit the region between
   `<!-- BEGIN track:board -->` and `<!-- END track:board -->`. Commit it following the repo's
   commit conventions (check `git log`) with a real body.
7. Remove the worktree once its story is integrated (`git worktree remove <path>`) to reclaim its
   build artifacts. Keep the branch.
8. **Never push.**

## 5 · Report

End with one table and nothing padded around it:

| Story | Verdict | Merge | Gate | Notes |
|---|---|---|---|---|

Then, explicitly: what was parked and why · what you could not run · anything you decided that the
user might have decided differently · and the push command, unrun:

```
git push origin <branch>
```

## Rules that override convenience

- You do not implement. Merge-conflict resolution and the ledger commit are the only code you write.
- No claim of done without the gate output to back it. If a command did not run, say which and why.
- Uncommitted work you did not create is precious. It is never in your way; you are in its way.
- A parked story is a successful outcome with a note attached. A silently dropped story is not.
