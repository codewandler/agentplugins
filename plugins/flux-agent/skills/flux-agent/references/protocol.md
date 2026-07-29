# The flux NDJSON protocol, as observed

`flux run --stream-json` emits one `\n`-terminated JSON object per line on stdout, flushed per line.
Every line carries a `type` tag and a schema version `v`. Diagnostics go to stderr, so stdout stays
`jq`-parseable with no filtering.

**`v: 1` is explicitly unstable.** The tag set is open and additive: a consumer **must skip an
unrecognised `type` rather than error**. Field shapes within a version are not yet promised stable.

Enable it with `--stream-json`. To also feed turns in over stdin use `--stream-json-input`, which
**requires `--yes`** (its stdin reader and the interactive approval prompt would otherwise race on
the same fd). Not supported for `flux run <app.flux>`.

## Line vocabulary

Captured from a real run (`read` + `write` task, OpenRouter provider):

| `type` | Fields | Notes |
|---|---|---|
| `turn_start` | `session`, `model`, `input` | First line. `model` is the resolved spec, vendor prefix stripped |
| `plan` | `session`, `data` | The proposed action batch — `batch_id`, `actions`, `risk`. Only for batched work |
| `approval` | `session`, `phase`, `data` | `phase` ∈ `requested` / `approved` / `denied`. Batch-level, so no single `tool` field |
| `tool_call` | `session`, `name`, `input` | One per op dispatched |
| `tool_result` | `session`, `name`, `is_error`, `content`, `view`, `duration_us` | Paired with the preceding `tool_call` |
| `steered` | `session`, `messages` | Mid-turn steering was folded in |
| `turn_end` | `session`, `answer`, `usage`, `cost_usd` | Last line |
| `error` | `session`, `message` | Sourced from `run_turn`'s `Err(_)` — see the gap below |

Observed ordering note: `tool_call` / `tool_result` for early exploration ops can precede the `plan`
line, because exploration runs before a batch is proposed. Do not assume `plan` comes first.

## What is safe to key on

**Safe:**
- `type` for stream structure.
- `tool_call.name` / `tool_result.is_error` for per-op outcomes.
- `turn_end.cost_usd` and `usage` **on a successful turn**, for accounting.
- `session`, to correlate lines and to find the run later via `flux sessions`.

**Not safe:**
- **The process exit code.** 0 on a failed turn (flux C-226).
- **The presence of `turn_end`.** A failed turn emits an ordinary one.
- **The absence of `error`.** It does not fire for stage/provider failures.
- **`usage == null`** as a failure test. It correlates today but is a coincidence of the failure
  path, not a contract — flux's own C-226 acceptance says so explicitly.

## The gap you must code around

A model- or flow-level failure inside a turn is **not** a distinct signal. `LoopHost::detect_intent`
and `LoopHost::explore` (`crates/flux-flow/src/loop_host.rs`) convert a stage `Err` into an `Ok`
value tagged `kind: "error"`, whose text becomes the turn's answer. So the failure arrives as prose:

```json
{"type":"turn_start","v":1,"session":"s_1627","model":"anthropic/claude-haiku-4.5","input":"say hi"}
{"type":"turn_end","v":1,"session":"s_1627","answer":"Intent detection failed: api error (status 401): {\"error\":{\"message\":\"User not found.\",\"code\":401}}","usage":null,"cost_usd":null}
```

Exit code 0. Nothing on stderr. Reproduce deterministically with a bogus key:

```bash
OPENROUTER_API_KEY=sk-or-v1-bogus flux run --yes --stream-json \
  -m openrouter/anthropic/claude-haiku-4.5 "say hi"; echo "EXIT=$?"
```

Until flux C-226 lands, detection means matching the answer text against known stage-failure
prefixes — `Intent detection failed:`, `Exploration failed:`, `I couldn't complete the turn` — and
then classifying the reason. `flux_run.py` does this; keep its pattern lists as the single place
that knowledge lives.

**When C-226 lands**, `turn_end` should carry a typed `outcome` and the `error` line should fire.
Prefer those and demote the string matching to a fallback — `_classify()` in `flux_run.py` is
already structured so the typed signal wins when present.

## Related flux stories

Epic `unattended-run-integrity` (`docs/designs/unattended-run-integrity.md`):

- **C-226** — a failed turn is indistinguishable from a successful one.
- **C-227** — no automatic resume for a transport-class failure.
- **C-228** — Gemini 3.x over OpenRouter drops the stream mid-exploration.

The epic's ordering constraint matters to consumers too: C-228 must be diagnosed before C-227's
retry behaviour is trusted, because retrying a deterministic codec bug looks exactly like retrying a
flaky network while burning budget.
