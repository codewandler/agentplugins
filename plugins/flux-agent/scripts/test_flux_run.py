#!/usr/bin/env python3
"""Offline tests for flux_run.py's failure classification.

No network, no flux binary, no API key. Run: python3 test_flux_run.py

Classification is the whole value of the wrapper — a misclassified failure
either retries an auth error in a loop or gives up on a recoverable one — so it
is the part that gets tested.
"""

import importlib.util
import sys
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "flux_run", Path(__file__).with_name("flux_run.py")
)
fr = importlib.util.module_from_spec(_spec)
sys.modules["flux_run"] = fr          # dataclasses needs the module registered
_spec.loader.exec_module(fr)

FAILURES: list[str] = []


def check(label: str, got, want) -> None:
    if got == want:
        print(f"  PASS  {label}")
    else:
        print(f"  FAIL  {label}: got {got!r}, want {want!r}")
        FAILURES.append(label)


def test_classification() -> None:
    print("classification of turn_end.answer:")
    cases = [
        # A real answer is a real turn.
        ("Done. result.txt now contains the output.", "ok"),
        # Task-class: retrying never converges.
        ("Intent detection failed: api error (status 401): User not found.", "task"),
        ("Exploration failed: no such model", "task"),
        ("I couldn't complete the turn — flow store: database or disk is full", "task"),
        # Transport-class: retrying is meaningful.
        ("Exploration failed: provider error: api_error: stream closed before completion", "transport"),
        ("Exploration failed: provider error: rate_limit_error: temporarily rate-limited upstream", "transport"),
        # Unknown stage failure: retry once, but never silently call it fine.
        ("Exploration failed: something nobody has seen before", "transport"),
    ]
    for text, want in cases:
        got, _ = fr._classify(text, None, None)
        check(text[:58], got, want)


def test_answer_is_not_failure_just_because_usage_is_null() -> None:
    print("usage=None alone must not mean failure (it is not a contract):")
    got, _ = fr._classify("Here is your answer.", None, None)
    check("plain answer + usage=None", got, "ok")


def test_typed_error_line_wins() -> None:
    print("an explicit NDJSON error line outranks answer-text sniffing:")
    got, _ = fr._classify("", None, "stream closed before completion")
    check("transport error line", got, "transport")
    got, _ = fr._classify("", None, "api error (status 401)")
    check("task error line", got, "task")


def test_fingerprint() -> None:
    print("fingerprinting (same bug at different depths must match):")
    a = "stream closed before completion at ctx 12000 session s_1617"
    b = "stream closed before completion at ctx 21100 session s_1618"
    c = "rate_limit_error upstream"
    check("same bug, different numbers", fr._fingerprint(a), fr._fingerprint(b))
    check("different bug differs", fr._fingerprint(a) != fr._fingerprint(c), True)


if __name__ == "__main__":
    test_classification()
    test_answer_is_not_failure_just_because_usage_is_null()
    test_typed_error_line_wins()
    test_fingerprint()
    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILED: {FAILURES}")
        sys.exit(1)
    print("all tests passed")
