# Testing & Quality

Rust builds testing into the language and toolchain. The expert stack in 2026: **nextest** (runner) +
**criterion/divan** (bench) + **proptest** (property) + **insta** (snapshot) + **rstest**
(fixtures/params) + **mockall** (mocks) + **cargo-llvm-cov** (coverage) + **Miri** (UB).

## The three kinds of test

| Kind | Location | Sees | Use for |
|---|---|---|---|
| **Unit** | `#[cfg(test)] mod tests` in the source file | Private items | Internal logic (the only way to test private items) |
| **Integration** | `tests/*.rs` (each file is its own crate) | Public API only | The public contract, as a downstream user sees it |
| **Doc** | `///` examples | Public API | Keeping docs honest (they compile & run) |

```rust
fn add(a: u64, b: u64) -> u64 { a + b }

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn adds() -> Result<(), std::num::ParseIntError> {   // Result-returning: use ? not unwrap
        let n: u64 = "40".parse()?;
        assert_eq!(add(n, 2), 42, "expected 40 + 2");    // custom message for context
        Ok(())
    }

    #[test]
    #[should_panic(expected = "overflow")]                // only for contract panics
    fn rejects_overflow() { add(u64::MAX, 1); }
}
```

**Integration test with a shared helper** — put helpers in `tests/common/mod.rs` (a subdirectory
module), **not** `tests/common.rs`, or the helper is collected as its own spurious test crate:

```rust
// tests/api.rs
mod common;                        // pulls in tests/common/mod.rs
use widget_core::parse;            // public API only

#[test]
fn parses_via_public_api() {
    common::setup();
    assert!(parse("gizmo").is_ok());
}
```

Prefer **`Result`-returning tests** with `?` over `.unwrap()`; reserve `#[should_panic(expected=..)]`
for panics that are part of the contract. Use `#[ignore = "reason"]` for slow/optional tests.

## Test runner & async

Use **`cargo-nextest`** (`cargo nextest run`): process-per-test isolation, faster scheduling, flake
retries, CI sharding, JUnit output. **Caveat:** nextest does **not** run doc tests — run
`cargo test --doc` separately.

Test async code with `#[tokio::test]` (use `flavor = "multi_thread"` when you need real parallelism):

```rust
#[tokio::test]
async fn fetches() {
    let out = fetch("id-1").await.unwrap();
    assert_eq!(out.id, "id-1");
}
```

## Property, snapshot, mock

```rust
// Property-based: assert invariants over generated inputs (proptest shrinks failures).
use proptest::prelude::*;
proptest! {
    #[test]
    fn roundtrips(s in ".*") {
        prop_assert_eq!(decode(&encode(&s)), s);
    }
}

// Mock a trait dependency (design code against traits so tests inject deterministic doubles).
use mockall::automock;
#[automock]                        // generates MockStore
trait Store { fn get(&self, k: &str) -> Option<String>; }

#[test]
fn uses_store() {
    let mut m = MockStore::new();
    m.expect_get().returning(|_| Some("v".into()));
    assert_eq!(service(&m), "v");
}
```

- **`insta`** — snapshot testing of large/structured output; review with `cargo insta review`.
- **`rstest`** — fixtures and parameterized/table-driven cases.

## Benchmarking

The built-in `#[bench]` is a **hard error on stable** — use **`criterion`** (statistically rigorous,
HTML reports, regression detection) or `divan`. Wrap inputs in `std::hint::black_box` to defeat
const-folding, and set `harness = false`:

```rust
// benches/bench.rs
use criterion::{criterion_group, criterion_main, Criterion};
use std::hint::black_box;

fn bench(c: &mut Criterion) {
    c.bench_function("fib 20", |b| b.iter(|| fib(black_box(20))));
}
criterion_group!(benches, bench);
criterion_main!(benches);
```
```toml
[dev-dependencies]
criterion = "0.5"

[[bench]]
name = "bench"
harness = false          # criterion supplies its own harness
```

## Coverage, UB, CI

- Measure coverage with **`cargo-llvm-cov`** (LLVM source-based, accurate, cross-platform) over
  `cargo-tarpaulin` (Linux-x86_64-only) for new projects.
- Run **Miri** (`cargo +nightly miri test`) on any crate containing `unsafe` — it catches undefined
  behavior (invalid provenance, type-invariant violations, data races). "Tests pass" is **not**
  evidence of UB-freedom.
- CI should run: `fmt --check`, `clippy -D warnings`, `nextest run`, `test --doc`, an MSRV build,
  coverage, `cargo audit`/`cargo deny`, and Miri if the crate has `unsafe`.

## `unsafe` discipline

- Justify every `unsafe` — it must be *necessary* (FFI, a proven-safe optimization, a low-level data
  structure), never a shortcut around the borrow checker.
- **One unsafe operation per block, each with a `// SAFETY:` comment** stating the invariant and why
  it holds. `clippy::undocumented_unsafe_blocks` is an **error under Edition 2024**.
- Minimize the unsafe surface: keep blocks small, wrap them in a **safe abstraction** whose public API
  can't be misused, and document caller obligations under `# Safety` on any `pub unsafe fn`.

```rust
let first = {
    // SAFETY: `idx < slice.len()` is guaranteed by the `if` above, so the pointer
    // is in-bounds and the element is initialized.
    unsafe { slice.get_unchecked(idx) }
};
```

## MUST DO

- Put private-item tests in `#[cfg(test)] mod tests`; use integration tests for the public contract.
- Use `tests/common/mod.rs` for shared helpers (not `tests/common.rs`).
- Run doc tests explicitly when using nextest (`cargo test --doc`).
- `black_box` benchmark inputs and set `harness = false`.
- Give every `unsafe` block a single operation and a `// SAFETY:` comment; wrap it in a safe API.
- Run Miri on `unsafe`-containing crates; design against traits to enable mocking.

## MUST NOT DO

- Don't make items `pub` solely to test them — use integration tests for the public surface.
- Don't use `tests/common.rs` (it becomes a spurious test crate).
- Don't assume nextest covers doc tests.
- Don't trust benchmarks that let the compiler const-fold the work away, or rely on nightly `#[bench]`.
- Don't use `unsafe` to bypass the borrow checker, or batch several unsafe ops under one bare block.
- Don't treat "tests pass" as proof of UB-freedom; don't hard-wire concrete I/O into logic you must test.

## Quick Reference

| Task | Tool / pattern |
|---|---|
| Test private internals | `#[cfg(test)] mod tests` |
| Test public contract | `tests/*.rs` integration tests |
| Keep docs correct | doc tests (`///` examples) |
| Fast, isolated runner | `cargo nextest run` (+ `cargo test --doc`) |
| Async test | `#[tokio::test]` |
| Invariants over inputs | `proptest` |
| Structured-output regression | `insta` snapshots |
| Fixtures / parameterized | `rstest` |
| Mock a dependency | `mockall` `#[automock]` |
| Benchmark | `criterion` / `divan` + `black_box` |
| Coverage | `cargo-llvm-cov` |
| Detect UB in `unsafe` | Miri (`cargo +nightly miri test`) |
