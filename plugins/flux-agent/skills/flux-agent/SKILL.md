---
name: flux-agent
description: Drive the flux agent (codewandler/flux) as a sub-agent from Claude Code over its NDJSON protocol, reliably. Use when dispatching work to flux, running flux headlessly or in a loop, fanning implementation work out to flux workers, choosing a flux model/provider, or debugging a flux run that reported success but did nothing. Covers `flux run --stream-json`, failure classification, bounded resume, and the ground-truth rules that make an unattended flux run trustworthy.
---

# Driving flux as a sub-agent

`flux` is a Rust agent platform with a real safety envelope and a machine-readable line protocol.
That makes it a good target for delegated work — **once you stop trusting the things about it that
cannot currently be trusted.**

Everything below is derived from observed behaviour, not from documentation. Where flux has an open
gap, the story that tracks it is named so you can check whether it has since been fixed.

## The three rules

**1 · Never trust the exit code.** `flux run` exits **0** when a turn dies on a provider error. This
is not an edge case — a stage failure is converted into an ordinary `Ok` value
(`crates/flux-flow/src/loop_host.rs`, `detect_intent` / `explore`), so the process believes it
succeeded. Tracked as flux **C-226**.

**2 · Never trust `turn_end` alone.** The same failure arrives as a normal-looking `turn_end` whose
`answer` is an apology in prose:

```json
{"type":"turn_end","v":1,"answer":"Intent detection failed: api error (status 401): ...","usage":null,"cost_usd":null}
```

There is no `error` line for this class. `usage: null` correlates with failure but is **not** a
contract — do not key on it.

**3 · Ground truth is a predicate you evaluate yourself.** The only reliable answer to "did the work
happen" is to go and look: `git log --oneline main..impl/X`, the file exists, the test passes. Pass
it as `--success-cmd` and let it overrule anything the model or the protocol claims. A model
reporting "Done." while the predicate fails is the single most common failure mode, and this is what
catches it.

## Use the wrapper, not raw `flux run`

`scripts/flux_run.py` implements all three rules plus bounded resume. Prefer it over hand-rolling.

```bash
python3 scripts/flux_run.py \
  --cwd /path/to/worktree \
  --model openrouter/anthropic/claude-haiku-4.5 \
  --prompt-file ./task.md \
  --success-cmd 'git log --oneline main..HEAD' \
  --allow-bash \
  --max-attempts 6
```

It prints one JSON object and exits 0 **only** on verified success:

| `outcome` | Meaning | What to do |
|---|---|---|
| `success` | Predicate satisfied | Review the diff as evidence |
| `claimed_but_unverified` | Turn ended cleanly, predicate failed | **Treat as failure.** The model believes it finished; it did not |
| `deterministic_failure` | Same failure twice running | Stop. This is a bug, not a flaky network — retrying burns money |
| `failed` | Task-class (401, bad model, disk full) | Fix the cause; retrying never converges |
| `exhausted` | Attempts used up on transport errors | Provider is genuinely unhealthy |

Useful flags: `--allow-bash` sets `FLUX_ENABLE_BASH=1` (flux gates the generic `bash` op off by
default — a worker that must run a build/test gate needs it), `--timeout` per attempt,
`--flux-arg` to pass anything else through, `--log-dir` for the raw NDJSON of every attempt.

Test the classifier offline anytime with `python3 scripts/test_flux_run.py` — no network or key.

## Retry only what is worth retrying

Splitting failures correctly matters more than retrying hard:

- **Transport** (closed stream, 429/5xx, timeout) — resume with `--continue`. flux sessions are
  durable, so a resumed run keeps its work. Verified: a run that died at step 16 continued to step
  34 on resume.
- **Task** (401, unknown model, content policy, budget, disk full) — never retry. A loop here just
  spends money.
- **Repeating identically** — stop, even if it looks like transport. If flux's own codec is ending
  the stream, every attempt fails the same way at the same depth and the retry machinery disguises a
  fixable bug as a flaky network. flux's own `docs/designs/unattended-run-integrity.md` treats this
  as the load-bearing distinction; the wrapper enforces it via failure fingerprinting.

## Choosing a model

Measured on a real multi-step task over `openrouter`, not from a spec sheet:

| Model | Result |
|---|---|
| `openrouter/anthropic/claude-haiku-4.5` | Reliable. Good default for cheap delegated work |
| `openrouter/google/gemini-2.5-flash` | Explores fine; cheapest. Weak at multi-file editing |
| `openrouter/google/gemini-3.5-flash`, `3.6-flash` | **Avoid for long runs.** Reproducibly die with `stream closed before completion` at 12–21k ctx (flux **C-228**) |

Model spec form is `provider/model`, and for OpenRouter it is `openrouter/<vendor>/<model>`. Prompt
caching only applies to `anthropic/…` slugs.

**Match the model to the task.** A fast/cheap model is fine for exploration, summarising, or a
mechanical single-file edit. It is a poor choice for subtle multi-file work: an observed failure was
a fast model using an `append` op on a 2350-line Rust file, landing a test *after* the closing brace
of the test module. Review the diff, never the summary.

## Writing the task prompt

flux workers behave best with the same contract you would give any implementor:

- State the **single** task and that it should stop when done.
- Name the **gate** commands explicitly, and warn that a first cold build takes minutes so it is not
  abandoned.
- **Fence shared files** you will own yourself (changelogs, generated boards, lockfiles).
- Demand a report that separates *what was run* from *what was claimed* — then verify anyway.
- Warn that huge files must be read in ranges.

⚠ In a Rust repo, a stale committed `Cargo.lock` means *any* cargo invocation dirties it, so a
lockfile fence will trip through no fault of the worker. Check before blaming the diff.

## Isolation

Give each worker its own git worktree and scratch branch. flux confines its own file ops to the
working directory, but a subprocess it spawns (cargo, a test runner) is not confined unless you run
flux with `--sandbox`. Two workers in one checkout will corrupt each other.

Budget disk deliberately: each worktree pays its own cold build, which for a large Rust workspace is
tens of GB. Disk exhaustion surfaces as opaque compiler errors, or as flux failing with
`flow store: database or disk is full`.

## Further reference

- `references/protocol.md` — the observed NDJSON line vocabulary, field by field, and which fields
  are safe to key on.
