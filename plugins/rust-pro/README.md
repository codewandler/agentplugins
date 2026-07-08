# rust-pro — idiomatic Rust specialist for Claude Code

A reusable Claude Code plugin that turns any agent into a **senior Rust engineer**: memory-safe,
idiomatic, high-performance Rust targeting the **2024 edition** (Rust 1.85+). It packages a single
progressive-disclosure skill — a compact `SKILL.md` that routes to six deep, code-heavy references.

```
/plugin install rust-pro@agentplugins
```

## What it does

The skill sets the operating posture (lean on the type system and borrow checker as *design tools*),
then loads only the reference the current task needs:

| Reference | Covers |
|---|---|
| `references/ownership.md` | Move/Copy/borrow/clone, lifetimes & elision, `Box`/`Rc`/`Arc`/`RefCell`/`Cow`, `Weak` cycles |
| `references/error-handling.md` | `Result`/`?`, `thiserror` (libraries) vs `anyhow` (apps), `Error` contract, panic policy |
| `references/traits-generics.md` | Trait design, static vs `dyn` dispatch, dyn compatibility, conversions, builder & typestate, async traits |
| `references/async-concurrency.md` | Tokio, `Send`/`Sync`, channels, `select!`/`JoinSet`, `rayon`, scoped threads, the "no lock across `.await`" rule |
| `references/testing.md` | Unit/integration/doc tests, `nextest`, `proptest`, `criterion`, Miri, `unsafe` review |
| `references/project-structure.md` | Cargo workspaces, feature flags, MSRV/resolver v3, `clippy`/`rustfmt`, edition-2024 changes, release profiles |

## Design principles it enforces

- **Make illegal states unrepresentable** — newtypes, enums over bools/strings, typestate.
- **Borrow before cloning**; the weakest sharing primitive that works; `Arc` (not `Rc`) across threads.
- **Zero-cost static dispatch by default**; `dyn` only for genuine heterogeneity.
- **Typed, matchable library errors** (`thiserror`); type-erased context at the app boundary (`anyhow`).
- **A green gate**: `cargo fmt`, `cargo clippy -- -D warnings`, `cargo nextest run` + `cargo test --doc`.
- **Small `unsafe` surfaces** with `// SAFETY:` comments, verified with Miri.

## Currency

Written against the Rust 2024 edition (shipped with Rust 1.85, Feb 2025) and the mid-2026 ecosystem:
`async fn` in traits is stable (1.75+) but not `dyn`-compatible; async-std is discontinued
(RUSTSEC-2025-0052) and Tokio is the default runtime; the built-in `#[bench]` is gone from stable
(use `criterion`/`divan`); lints are centralized via the `[lints]` table.

## License

MIT
