# Flux Agent — drive flux as a sub-agent

Dispatch work to [flux](https://github.com/codewandler/flux) from Claude Code over its NDJSON line
protocol, and get an answer you can actually trust.

## Why

flux is a good delegation target — real safety envelope, durable sessions, a machine-readable
protocol. But driving it unattended today has a sharp edge:

```console
$ OPENROUTER_API_KEY=bogus flux run --yes --stream-json -m openrouter/anthropic/claude-haiku-4.5 "say hi"
{"type":"turn_start", ...}
{"type":"turn_end","answer":"Intent detection failed: api error (status 401): ...","usage":null,"cost_usd":null}
$ echo $?
0
```

**Exit code 0. A normal-looking `turn_end`. No `error` line. Nothing on stderr.** A stage failure is
converted into an `Ok` value inside flux, so nothing downstream can tell it from success. Add that a
dropped provider stream ends a long run outright with no retry, and an unattended flux run is a coin
flip that reports heads either way.

This plugin encodes the workarounds so you don't rediscover them mid-task.

## What's here

| Path | What it is |
|---|---|
| `skills/flux-agent/SKILL.md` | The trust rules, model selection, prompt and isolation discipline |
| `skills/flux-agent/references/protocol.md` | Observed NDJSON vocabulary, field by field, and what is safe to key on |
| `scripts/flux_run.py` | The wrapper: NDJSON, failure classification, bounded resume, verified outcome |
| `scripts/test_flux_run.py` | Offline tests for the classifier — no network, no key, no flux binary |

## Quick start

```bash
python3 scripts/flux_run.py \
  --cwd /path/to/worktree \
  --model openrouter/anthropic/claude-haiku-4.5 \
  --prompt-file ./task.md \
  --success-cmd 'git log --oneline main..HEAD' \
  --allow-bash
```

Prints one JSON result and exits 0 **only** when the success predicate is satisfied:

```json
{
  "outcome": "success",
  "attempt_count": 1,
  "total_cost_usd": 0.029428,
  "ops_executed": ["read", "write"],
  "final_answer": "...",
  "log_dir": "/path/to/worktree/.flux-run-logs"
}
```

Outcomes: `success` · `claimed_but_unverified` (model says done, predicate disagrees — treat as
failure) · `deterministic_failure` (same error twice; stop rather than burn budget) · `failed`
(task-class, never retryable) · `exhausted`.

## The rules it enforces

1. **The exit code lies.** Never key on it.
2. **A clean `turn_end` lies.** Failures arrive as prose in `answer`.
3. **Ground truth is a predicate you evaluate yourself.** `--success-cmd` overrules every claim.
4. **Retry transport, never task** — and stop on a failure that repeats identically, because that is
   a deterministic bug wearing a flaky network's clothes.

## Requirements

`flux` on `PATH`, Python 3.9+, and a configured provider (`flux auth status`).

## Upstream

Tracked in flux under epic `unattended-run-integrity`: **C-226** (failed turn indistinguishable from
success), **C-227** (no automatic resume), **C-228** (Gemini 3.x drops the stream over OpenRouter).
As those land, prefer flux's typed signals and demote this wrapper's string matching to a fallback —
`_classify()` is already structured for that.
