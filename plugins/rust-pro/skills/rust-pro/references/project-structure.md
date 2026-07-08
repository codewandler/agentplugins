# Project Structure & Tooling

Cargo and the surrounding toolchain do the mechanical work so review effort goes to design. The
expert baseline: a workspace with **centralized versions/lints**, **Edition 2024** (resolver v3), and
a green `fmt` + `clippy -D warnings` + `nextest` gate in CI.

## Two independent version numbers

- **Edition** — a per-crate opt-in (`edition = "2024"`); controls language semantics.
- **Toolchain / MSRV** — the `rustc` you compile with (`rust-version` = minimum supported).

They're independent: a 2021-edition crate compiles fine with a 2026 toolchain. Don't conflate them.

## Workspace layout

Use a **virtual workspace** (root `Cargo.toml` with `[workspace]` and *no* `[package]`) for multi-crate
repos. Keep binaries thin: logic in `src/lib.rs`, `src/main.rs` a shell that calls it — binaries can't
be integration-tested, libraries can.

```toml
# Root Cargo.toml (virtual workspace)
[workspace]
resolver = "3"                       # MSRV-aware; implied by edition 2024 but set it explicitly
members  = ["crates/*"]

[workspace.package]                  # inherited metadata — single source of truth
edition      = "2024"
rust-version = "1.85"                # the workspace MSRV
license      = "MIT OR Apache-2.0"
repository   = "https://github.com/acme/widget"

[workspace.dependencies]             # single source of truth for versions
serde  = { version = "1", features = ["derive"] }
tokio  = { version = "1", features = ["rt-multi-thread", "macros"] }
anyhow = "1"

[workspace.lints.rust]
unsafe_code  = "forbid"              # or "deny" with per-block opt-out
missing_docs = "warn"

[workspace.lints.clippy]
all      = { level = "warn", priority = -1 }   # group at low priority...
pedantic = { level = "warn", priority = -1 }   # ...so specific lints can override
module_name_repetitions = "allow"              # opt out of individual pedantic lints
```

```toml
# Member crate Cargo.toml — inherit everything
[package]
name = "widget-core"
version = "0.1.0"
edition.workspace      = true
rust-version.workspace = true
license.workspace      = true

[dependencies]
serde   = { workspace = true }
anyhow  = { workspace = true }
tracing = { version = "0.1", optional = true }

[features]
default    = ["std"]
std        = []
logging    = ["dep:tracing"]                 # dep: hides the implicit `tracing` feature
serde-json = ["dep:serde_json", "serde?/std"] # weak dep: only if serde is already enabled

[lints]
workspace = true                             # inherit the workspace lint config
```

> **Note:** `resolver = "3"` is a workspace-global setting and is **not** inferred from member
> editions — set it in the virtual-workspace root explicitly. Centralize versions with
> `cargo-autoinherit` on existing workspaces.

## Feature flags — must be additive

Enabling a feature only **adds** capability, never removes or changes it. Design around a `std`
feature (on by default), never a subtractive `no_std` feature.

- Use `dep:` to hide an optional dependency from becoming an implicit feature.
- Use `crate?/feature` (weak deps) to enable a dep's feature *only if* that dep is already enabled.
- Name features by capability, not implementation. **Removing a default feature is a SemVer break.**
- Avoid mutually-exclusive features; if unavoidable, guard with `compile_error!`.

## Module system & visibility

- Prefer `mod foo;` with `src/foo.rs` and submodules at `src/foo/bar.rs` — the 2018+ path model.
  `mod.rs` is legacy and no longer required.
- Default to **private**; widen deliberately: `pub(crate)` for crate-internal, `pub(super)` /
  `pub(in path)` for narrow scoping, `pub` only for the intended public surface.
- Curate the public API with re-exports (`pub use`) so callers write `mycrate::Thing` regardless of
  internal layout. Offer a `prelude` module for glob-importable common items.
- No `extern crate` in 2018+ (except `#[macro_use]` niches and `alloc`/`std` in `no_std`); paths start
  with the crate name or `crate::`/`self::`/`super::`.

## Tooling baseline (non-negotiable)

- `cargo fmt` (rustfmt) with a checked-in `rustfmt.toml`, enforced as `cargo fmt --check` in CI.
- `cargo clippy -- -D warnings` in CI; `cargo check` in the fast inner loop.
- Configure lints **centrally** in `[lints]` / `[workspace.lints]` (stable since 1.74) — the modern
  idiom, honored by rust-analyzer — not scattered crate attributes.
- Turn on `clippy::pedantic` at **`warn`** (not `deny`) and cherry-pick from `nursery`/`restriction`;
  never enable `nursery` or `restriction` wholesale.
- Declare **MSRV** with `rust-version`; the resolver v3 then picks compatible dependency versions.
  Pin the *dev* toolchain separately with `rust-toolchain.toml`.
- Supply-chain gates in CI: `cargo audit` (RustSec advisories) and `cargo deny check` (licenses,
  bans, duplicates, sources). Runner: `cargo nextest`.

```toml
# rust-toolchain.toml — pins the dev toolchain (distinct from MSRV)
[toolchain]
channel    = "1.89.0"
components = ["rustfmt", "clippy"]
profile    = "minimal"
```

### Clippy category model

| Category | Default | Guidance |
|---|---|---|
| `correctness` | **deny** | Almost-certainly-wrong; keep denied |
| `suspicious` / `style` / `complexity` / `perf` | warn | Actionable — fix them |
| `pedantic` | allow | Opt in at `warn`; expect some false positives |
| `nursery` | allow | Experimental — cherry-pick only |
| `restriction` | allow | Blanket bans (`unwrap_used`, `as_conversions`) — opt in **individually**, never wholesale |
| `cargo` | allow | `Cargo.toml` hygiene |

## Edition migration

Run `cargo fix --edition` **before** bumping the `edition` key, one step at a time
(2015 → 2018 → 2021 → 2024), then bump it. Review `Drop`-timing-sensitive lints
(`tail_expr_drop_order`, `if_let_rescope`) by hand — they can change semantics.

## Release profile & docs

```toml
[profile.release]
opt-level     = 3
lto           = "fat"      # whole-program; "thin" for faster links
codegen-units = 1          # best optimization, slowest compile
panic         = "abort"    # smaller/faster; drops unwinding (tests still unwind)
strip         = "symbols"

[profile.release-with-debug]   # for perf/flamegraph work
inherits = "release"
debug    = true
strip    = "none"
```

Every public item gets a `///` doc comment; crate/module docs use `//!`. Use compiler-checked
**intra-doc links** (`` [`Type`] ``) and conventional `# Examples` / `# Errors` / `# Panics` /
`# Safety` sections. Doc examples compile and run as tests by default — and use `?`, never `unwrap()`
(C-QUESTION-MARK).

```rust
/// Parses a widget from `input`.
///
/// # Examples
/// ```
/// let w = widget_core::parse("gizmo")?;
/// assert_eq!(w.name(), "gizmo");
/// # Ok::<(), widget_core::Error>(())
/// ```
///
/// # Errors
/// Returns [`Error::Malformed`] if `input` is not valid UTF-8.
pub fn parse(input: &str) -> Result<Widget, Error> { /* ... */ }
```

## What Edition 2024 changed (highlights)

- **Resolver v3 (MSRV-aware)** implied by edition 2024.
- `unsafe extern` blocks required; `#[unsafe(no_mangle)]` / `#[unsafe(export_name)]` /
  `#[unsafe(link_section)]` wrapping required.
- `unsafe_op_in_unsafe_fn` warns by default (wrap unsafe ops in explicit `unsafe { }`).
- RPIT `impl Trait` captures **all** in-scope generics/lifetimes by default (use `+ use<...>` to opt out).
- References to `static mut` are a hard error (use atomics / `OnceLock` / `Mutex`, or `&raw const/mut`).
- `if let` and tail-expression temporary drop scopes tightened (temporaries drop sooner).
- `gen` reserved as a keyword; `Future`/`IntoFuture` added to the prelude.

## MUST DO

- Run `cargo fmt --check`, `cargo clippy -- -D warnings`, and `cargo check` in CI; keep them green.
- Centralize versions/metadata/lints via workspace inheritance.
- Set `resolver = "3"` explicitly in a virtual-workspace root.
- Keep features additive; use `dep:`/weak features for optional deps.
- Declare `rust-version` (MSRV) and test it in CI; pin the dev toolchain separately.
- Run `cargo fix --edition` before bumping the edition, one step at a time.

## MUST NOT DO

- Don't hand-duplicate dependency versions across members.
- Don't create subtractive (`no_std`-style) or mutually-exclusive features without a `compile_error!` guard.
- Don't conflate MSRV with the pinned dev toolchain.
- Don't enable `clippy::nursery`/`restriction` wholesale, or set `pedantic` to `deny` in a shared crate.
- Don't use legacy `extern crate` or `mod.rs` layouts in new code.
- Don't ship `#![deny(warnings)]` in a published crate — a new compiler's warnings become build breaks downstream.

## Quick Reference

| Concern | Setting / tool |
|---|---|
| Multi-crate repo | Virtual workspace, `members = ["crates/*"]` |
| One version source | `[workspace.dependencies]` + `dep.workspace = true` |
| One lint source | `[workspace.lints]` + `[lints] workspace = true` |
| Dependency resolution | `resolver = "3"` (MSRV-aware) |
| Minimum Rust | `rust-version` (MSRV) |
| Pinned dev toolchain | `rust-toolchain.toml` |
| Format | `cargo fmt --check` |
| Lint | `cargo clippy -- -D warnings` |
| Security audit | `cargo audit`, `cargo deny check` |
| Edition upgrade | `cargo fix --edition` then bump |
| Optional dependency | `feature = ["dep:foo"]` |
