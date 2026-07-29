#!/usr/bin/env python3
"""Drive one `flux run` turn over the NDJSON protocol and report a typed result.

Why this exists: `flux run` cannot currently tell a caller that a turn failed.
A provider error is laundered into an ordinary-looking `turn_end` whose `answer`
is an apology, `usage` is null, and the process exits 0 (flux C-226). A dropped
stream ends a long run outright, with no retry (flux C-227). Driving flux as a
sub-agent therefore means reconstructing the outcome from the stream plus an
out-of-band ground truth.

This wrapper does exactly that and nothing else:

  * speaks `--stream-json` instead of scraping rendered prose;
  * classifies a failure as TRANSPORT (retryable) or TASK (never retryable);
  * resumes a transport failure with `flux run --continue`, bounded, with backoff;
  * treats a caller-supplied success predicate as ground truth over anything the
    model or the protocol claims;
  * emits one JSON object describing what actually happened, including the ops
    executed and the summed cost across every attempt.

Exit code: 0 if the run succeeded, 1 otherwise. Unlike flux's own, it is trustworthy.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Iterator

# --- Failure classification -------------------------------------------------
#
# These patterns are matched against the *answer text* of a turn, because that
# is where flux currently puts stage failures (crates/flux-flow/src/loop_host.rs
# converts a stage `Err` into an `Ok` value tagged kind=error, whose text lands
# in `turn_end.answer`). When flux C-226 lands and `turn_end` carries a typed
# outcome, `_classify` should prefer that field and keep these as a fallback.

# A stage died. The text after the prefix says why; that decides the class.
STAGE_FAILURE_PREFIXES = (
    "Intent detection failed:",
    "Exploration failed:",
    "I couldn't complete the turn",
)

# Transport: the connection or the upstream failed us. Retrying is meaningful.
TRANSPORT_PATTERNS = (
    r"stream closed before completion",
    r"rate[_ ]limit",
    r"\b429\b",
    r"\b50[0234]\b",
    r"overloaded",
    r"timed? ?out",
    r"connection (reset|refused|closed)",
    r"temporarily",
)

# Task: the request itself is wrong or refused. Retrying burns money and time
# and never converges. Keep this list ahead of TRANSPORT when both match.
TASK_PATTERNS = (
    r"\b401\b",
    r"\b403\b",
    r"\b404\b",
    r"User not found",
    r"invalid[_ ]api[_ ]key",
    r"no such model",
    r"not a valid model",
    r"budget",
    r"content[_ ]policy",
    r"max[_ ]iterations",
    # Environmental, but retrying cannot fix it and the loop would mask it.
    r"disk is full",
    r"no space left",
)


def _fingerprint(reason: str) -> str:
    """Normalise a failure reason so two runs of the same bug compare equal.

    Digits are dropped because the same deterministic failure reports different
    context depths / session ids each attempt.
    """
    return re.sub(r"\d+", "#", (reason or "").lower())[:160]


def _matches(text: str, patterns: tuple[str, ...]) -> str | None:
    for p in patterns:
        if re.search(p, text, re.IGNORECASE):
            return p
    return None


@dataclass
class Attempt:
    n: int
    outcome: str          # "ok" | "transport" | "task" | "no_turn_end" | "spawn_error"
    reason: str = ""
    answer: str = ""
    ops: list[str] = field(default_factory=list)
    cost_usd: float | None = None
    exit_code: int | None = None
    log: str = ""


def _classify(answer: str, usage: Any, saw_error_line: str | None) -> tuple[str, str]:
    """Return (outcome, reason) for one completed turn.

    `saw_error_line` is flux's typed `error` line if it ever fires. It does not
    fire for stage failures today, but when C-226 lands it should, and it wins.
    """
    if saw_error_line:
        cls = "task" if _matches(saw_error_line, TASK_PATTERNS) else "transport"
        return cls, saw_error_line

    text = (answer or "").strip()
    is_stage_failure = any(text.startswith(p) for p in STAGE_FAILURE_PREFIXES)

    if not is_stage_failure:
        # A turn that produced an answer and accounted usage is a real turn.
        # `usage is None` alone is NOT treated as failure: it is a coincidence of
        # the current failure path, not a contract (flux C-226 acceptance says so).
        return "ok", ""

    if _matches(text, TASK_PATTERNS):
        return "task", text
    if _matches(text, TRANSPORT_PATTERNS):
        return "transport", text
    # A stage failed for a reason we do not recognise. Retry once rather than
    # give up silently, but say plainly that the class is unknown.
    return "transport", f"unclassified stage failure: {text}"


def _stream(proc: subprocess.Popen, log_path: str) -> Iterator[dict]:
    """Yield parsed NDJSON objects, teeing every raw line to `log_path`."""
    with open(log_path, "w", encoding="utf-8") as log:
        assert proc.stdout is not None
        for raw in proc.stdout:
            log.write(raw)
            log.flush()
            line = raw.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                # A non-JSON line on a --stream-json stdout is a flux bug, not
                # ours. Record it and keep going; never let it kill the run.
                yield {"type": "_unparseable", "raw": line[:500]}


def run_attempt(
    n: int,
    cwd: str,
    model: str,
    prompt: str,
    log_dir: str,
    resume: bool,
    timeout: int,
    allow_bash: bool,
    extra_args: list[str],
    on_event=None,
) -> Attempt:
    cmd = ["flux", "run", "--yes", "--stream-json", "-m", model]
    if resume:
        cmd.append("--continue")
    cmd += extra_args
    cmd.append(prompt)

    env = dict(os.environ)
    if allow_bash:
        # flux gates the generic `bash` op behind an off-by-default group; an
        # implementor that must run a build/test gate needs it turned on.
        env["FLUX_ENABLE_BASH"] = "1"

    log_path = os.path.join(log_dir, f"attempt-{n}.ndjson")
    try:
        proc = subprocess.Popen(
            cmd, cwd=cwd, env=env, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, bufsize=1,
        )
    except FileNotFoundError:
        return Attempt(n=n, outcome="spawn_error", reason="`flux` not found on PATH")

    answer, usage, cost, ops, err_line = "", None, None, [], None
    deadline = time.monotonic() + timeout

    try:
        for obj in _stream(proc, log_path):
            if on_event:
                on_event(obj)
            t = obj.get("type")
            if t == "tool_call":
                ops.append(obj.get("name", "?"))
            elif t == "error":
                err_line = obj.get("message", "error")
            elif t == "turn_end":
                answer = obj.get("answer") or ""
                usage = obj.get("usage")
                cost = obj.get("cost_usd")
            if time.monotonic() > deadline:
                proc.kill()
                return Attempt(n=n, outcome="transport", reason="wrapper timeout",
                               ops=ops, log=log_path)
        code = proc.wait(timeout=30)
    except Exception as exc:  # noqa: BLE001 - report, never crash the driver
        proc.kill()
        return Attempt(n=n, outcome="transport", reason=f"stream read failed: {exc}",
                       ops=ops, log=log_path)

    if answer == "" and err_line is None:
        # No turn_end at all: flux died before finishing. Exit code is not
        # reliable here either, so classify on absence.
        return Attempt(n=n, outcome="no_turn_end", reason="no turn_end line emitted",
                       ops=ops, exit_code=code, log=log_path)

    outcome, reason = _classify(answer, usage, err_line)
    return Attempt(n=n, outcome=outcome, reason=reason, answer=answer, ops=ops,
                   cost_usd=cost, exit_code=code, log=log_path)


def success_predicate_met(cmd: str | None, cwd: str) -> bool | None:
    """Ground truth, independent of anything flux or the model reports.

    Returns None when no predicate was supplied (caller accepts the stream's word).
    """
    if not cmd:
        return None
    r = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True)
    return r.returncode == 0 and bool(r.stdout.strip())


def main() -> int:
    ap = argparse.ArgumentParser(description="Drive a flux turn reliably over NDJSON.")
    ap.add_argument("--cwd", required=True, help="working directory for the flux agent")
    ap.add_argument("--model", required=True, help="flux model spec, e.g. openrouter/anthropic/claude-haiku-4.5")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--prompt", help="prompt text")
    g.add_argument("--prompt-file", help="file containing the prompt")
    ap.add_argument("--resume-prompt", default=(
        "Your previous turn was cut short by a provider transport error, not by anything you did. "
        "Resume exactly where you left off and continue until the task is complete. Do not restart."
    ))
    ap.add_argument("--success-cmd", help=(
        "shell command evaluated in --cwd; non-zero exit or empty stdout means 'not done'. "
        "This is ground truth and overrides the stream. e.g. 'git log --oneline main..HEAD'"))
    ap.add_argument("--max-attempts", type=int, default=6)
    ap.add_argument("--timeout", type=int, default=3600, help="per-attempt seconds")
    ap.add_argument("--log-dir", default=None)
    ap.add_argument("--allow-bash", action="store_true", help="set FLUX_ENABLE_BASH=1")
    ap.add_argument("--quiet", action="store_true", help="no progress on stderr")
    ap.add_argument("--flux-arg", action="append", default=[],
                    help="extra arg passed through to flux run (repeatable)")
    args = ap.parse_args()

    prompt = args.prompt
    if args.prompt_file:
        with open(args.prompt_file, encoding="utf-8") as fh:
            prompt = fh.read()

    log_dir = args.log_dir or os.path.join(args.cwd, ".flux-run-logs")
    os.makedirs(log_dir, exist_ok=True)

    def progress(msg: str) -> None:
        if not args.quiet:
            print(f"[flux_run] {msg}", file=sys.stderr, flush=True)

    attempts: list[Attempt] = []
    total_cost = 0.0
    outcome = "failed"

    for n in range(1, args.max_attempts + 1):
        resume = n > 1
        progress(f"attempt {n}/{args.max_attempts}{' (--continue)' if resume else ''} · {args.model}")

        def on_event(obj: dict) -> None:
            if obj.get("type") == "tool_call":
                progress(f"  op: {obj.get('name')}")

        a = run_attempt(
            n=n, cwd=args.cwd, model=args.model,
            prompt=args.resume_prompt if resume else prompt,
            log_dir=log_dir, resume=resume, timeout=args.timeout,
            allow_bash=args.allow_bash, extra_args=args.flux_arg,
            on_event=None if args.quiet else on_event,
        )
        attempts.append(a)
        if a.cost_usd:
            total_cost += a.cost_usd
        progress(f"  -> {a.outcome} {('· ' + a.reason[:110]) if a.reason else ''}")

        # Ground truth first: the task can be complete even if the turn ended badly.
        done = success_predicate_met(args.success_cmd, args.cwd)
        if done:
            outcome = "success"
            break
        if a.outcome == "ok":
            # Stream says fine. Without a predicate we take its word; with one,
            # `done is False` means the model claimed completion it did not do.
            if done is None:
                outcome = "success"
                break
            outcome = "claimed_but_unverified"
            progress("  turn ended cleanly but the success predicate is not met")
            break
        if a.outcome in ("task", "spawn_error"):
            outcome = "failed"
            progress("  task-level failure — not retryable, stopping")
            break

        # A "transport" failure that repeats identically is not transport at all:
        # it is a deterministic bug being re-run. Retrying it burns budget and
        # real money and disguises a fixable defect as a flaky network, so stop
        # and say which it was. (flux docs/designs/unattended-run-integrity.md
        # makes this the load-bearing distinction of the whole retry question.)
        if len(attempts) >= 2 and _fingerprint(a.reason) == _fingerprint(attempts[-2].reason):
            outcome = "deterministic_failure"
            progress("  identical failure twice — deterministic, not transport; stopping")
            break

        if n < args.max_attempts:
            backoff = min(60, 2 ** n)
            progress(f"  retryable — backing off {backoff}s")
            time.sleep(backoff)
    else:
        outcome = "exhausted"

    result = {
        "outcome": outcome,
        "model": args.model,
        "cwd": args.cwd,
        "attempts": [asdict(a) for a in attempts],
        "attempt_count": len(attempts),
        "total_cost_usd": round(total_cost, 6),
        "ops_executed": [op for a in attempts for op in a.ops],
        "success_predicate": args.success_cmd,
        "final_answer": attempts[-1].answer if attempts else "",
        "log_dir": log_dir,
    }
    print(json.dumps(result, indent=2))
    return 0 if outcome == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
