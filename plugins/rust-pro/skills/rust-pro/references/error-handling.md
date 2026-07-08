# Error Handling

Rust splits failure into two worlds: **recoverable** (`Result<T, E>`, propagate with `?`) and
**unrecoverable** (`panic!` — bugs and broken invariants). The central design decision is *library
vs application*: libraries expose typed, matchable errors; applications type-erase and add context.

## The core model

```rust
// Result for expected/recoverable failure; ? propagates and converts via From.
fn load(path: &str) -> Result<Config, ConfigError> {
    let text = std::fs::read_to_string(path)?;   // io::Error -> ConfigError via From
    let cfg = toml::from_str(&text)?;            // toml::Error -> ConfigError via From
    Ok(cfg)
}

// Option for "value may be absent" (not itself an error). Convert at the boundary:
fn first_word(s: &str) -> Result<&str, ParseError> {
    s.split_whitespace().next().ok_or(ParseError::Empty)
}

// main can return Result so ? works at the top level (Termination trait):
fn main() -> anyhow::Result<()> {
    let cfg = load("app.toml")?;
    run(cfg)?;
    Ok(())
}
```

`let ... else` is the idiomatic early return for a refutable binding; in Edition 2024 combine with
let-chains (`if let A = x && let B = y && cond`, stable since 1.88):

```rust
fn first_line(text: &str) -> anyhow::Result<&str> {
    let Some(line) = text.lines().next() else {
        anyhow::bail!("input was empty");
    };
    Ok(line)
}
```

## Libraries: `thiserror` — typed, matchable, chainable

Callers need to **match** on distinct failure modes, so expose a concrete enum that implements
`std::error::Error`. `thiserror` (2.x) derives `Display`, `Error`, source chaining, and the `From`
impls that `?` needs.

```rust
use thiserror::Error;

#[derive(Debug, Error)]
#[non_exhaustive]                                 // adding variants later isn't breaking
pub enum DataStoreError {
    #[error("data store disconnected")]
    Disconnect(#[from] std::io::Error),           // generates From<io::Error>, sets source()

    #[error("no data for key `{0}`")]
    Redaction(String),                            // {0} interpolates the tuple field

    #[error("invalid header (expected {expected}, found {found})")]
    InvalidHeader { expected: String, found: String },

    #[error(transparent)]                         // forward Display + source to the inner error
    Other(#[from] anyhow::Error),
}
```

| Attribute | Effect |
|---|---|
| `#[error("...")]` | The `Display` impl; supports `{field}` and `{0}` interpolation |
| `#[from]` | Generates `From` **and** marks the field as `source()` — makes `?` "just work" |
| `#[source]` | Marks a source field **without** generating `From` |
| `#[error(transparent)]` | Forwards `Display` and `source()` to the wrapped error (pass-through variants) |

## Applications: `anyhow` — type-erase and add context

At the top of a binary you mostly log or display the error and want ergonomic propagation. One
type-erasing `anyhow::Error` is ideal there.

```rust
use anyhow::{Context, Result, bail, ensure};

fn load_config(path: &str) -> Result<Config> {
    ensure!(!path.is_empty(), "config path must not be empty");  // guard -> early Err
    let text = std::fs::read_to_string(path)
        .with_context(|| format!("failed to read config from {path}"))?;  // adds a chain frame
    let cfg: Config = toml::from_str(&text)
        .context("config file is not valid TOML")?;
    if cfg.workers == 0 {
        bail!("workers must be >= 1");            // ad-hoc error, early return
    }
    Ok(cfg)
}
```

- `.context(..)` / `.with_context(|| ..)` attach human-readable frames; the whole chain prints.
- `bail!(..)` = `return Err(anyhow!(..))`; `ensure!(cond, ..)` = conditional bail.
- Recover a concrete type from an `anyhow::Error` with `err.downcast_ref::<DataStoreError>()`.

**The combination:** internal library crates define `thiserror` enums; `main.rs` aggregates them into
`anyhow::Result` and layers on context.

## Custom error type contract (Rust API Guidelines: C-GOOD-ERR)

Public error types **must** implement `std::error::Error` and should be `Send + Sync + 'static`:

- `Send` → returnable from `thread::spawn`.
- `Sync` → shareable across threads via `Arc`.
- `Send + Sync` → wrappable by `io::Error::new`.
- `'static` → enables `Error::downcast_ref` on trait objects.

`Display` messages are **lowercase with no trailing punctuation** (`"data store disconnected"`, not
`"Data store disconnected."`). `Debug` (derived) is for developer diagnostics. Always preserve the
underlying cause via `source()` (`#[from]`/`#[source]` wire this up).

## panic / unwrap / expect discipline

`panic!` (and `unwrap`/`expect`/`assert!`) is for **unrecoverable bugs and broken invariants**, not
ordinary failure. It is appropriate in:

- Tests (a panic is how a test fails), examples, and prototypes.
- Enforcing an invariant the type system can't encode, or a contract violation (a caller bug).
- Cases where continuing would be unsafe or insecure.

Prefer `expect("why it can't fail")` over `unwrap()` where a panic is justified — treat the string
as a **proof obligation** documenting the invariant:

```rust
let port: u16 = "8080".parse().expect("hardcoded port literal is valid");
```

Better still, encode invariants in types so downstream code needs no re-checking (a validating
constructor returning `Result`, or a newtype whose `new` guarantees the property). Enable
`clippy::unwrap_used` / `clippy::expect_used` (restriction group) in crates where panics are banned.

## MUST DO

- Implement `std::error::Error` on public error types; make them `Send + Sync + 'static`.
- Use `thiserror` (or hand-written enums) for **library** errors so callers can match; use `anyhow`/`eyre` for **application** top-level flow.
- Wire up source chains (`#[from]`/`#[source]` → `Error::source()`).
- Return `Result` for expected failures and propagate with `?`.
- Write `Display` messages lowercase, no trailing period.
- Prefer `expect("reason")` over `unwrap()`; mark evolving public error enums `#[non_exhaustive]`.

## MUST NOT DO

- Don't `.unwrap()`/`.expect()` on recoverable errors in library or long-running code (tests/examples/provably-infallible are the exceptions).
- Don't expose `anyhow::Error` or `Box<dyn Error>` in a **library's public API** — it robs callers of the ability to match.
- Don't use `()` or bare `String` as a public error type (no `Error` impl; breaks chaining and `?`).
- Don't `panic!` on ordinary conditions (bad input, missing file, network failure) — those are `Result`.
- Don't swallow the source when wrapping — preserve it via `source()`/`#[from]`.
- Don't use eager `unwrap_or(expensive())` — use `unwrap_or_else(|| ..)` / `ok_or_else` (`clippy::or_fun_call`).

## Recent / edition notes

- **Rust 1.81:** `Error` trait stabilized in `core` → usable in `#![no_std]`.
- **`?`-in-`main`:** stable via `Termination`; `fn main() -> anyhow::Result<()>` is idiomatic for binaries.
- **Rust 1.88:** let-chains stabilized (Edition 2024 only) — flattens nested `Option`/`Result` handling.
- **thiserror 2.x:** `no_std` support, refined `#[from]`/`#[backtrace]` behavior.
- **anyhow 1.x:** backtrace capture when `RUST_BACKTRACE` is set, `Chain` iterator over causes, `downcast` to recover concrete types.

## Quick Reference

| Situation | Reach for |
|---|---|
| Expected, recoverable failure | `Result<T, E>` + `?` |
| Value may be absent (not an error) | `Option<T>` |
| Absence is an error to the caller | `.ok_or(..)` / `.ok_or_else(..)` |
| Library error type | `thiserror` enum, `#[non_exhaustive]` |
| Application top-level flow | `anyhow::Result` + `.context(..)` |
| Add a message frame | `.context(..)` / `.with_context(\|\| ..)` |
| Early error return | `bail!` / `ensure!` / `let ... else` |
| Recover concrete type from erased error | `.downcast_ref::<T>()` |
| Provably-infallible unwrap | `.expect("why")` with a documented reason |
