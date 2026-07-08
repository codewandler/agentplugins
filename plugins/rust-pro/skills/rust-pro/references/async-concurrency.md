# Concurrency & Async

The compiler enforces thread safety through `Send`/`Sync`, so concurrency bugs that plague other
languages become compile errors. The expert reflexes: **message passing over shared state**, the
**weakest sharing primitive that works**, and **async only for many concurrent I/O-bound tasks** —
threads or `rayon` for CPU-bound work.

## Send + Sync — the safety foundation

- **`Send`** = ownership can move to another thread. **`Sync`** = `&T` is shareable across threads.
- Let the compiler derive them; **never** implement them manually except for audited FFI/raw-pointer
  types (C-SEND-SYNC), and add tests when you do.
- `Rc`/`RefCell` are `!Send`/`!Sync` (single-threaded); `Arc`/`Mutex` are the thread-safe versions.

## Shared state across threads

Share ownership with **`Arc<T>`**; share *mutable* state with **`Arc<Mutex<T>>`** or
**`Arc<RwLock<T>>`**. Use atomics (`AtomicUsize`, `AtomicBool`, …) for simple counters/flags instead
of a `Mutex`.

```rust
use std::sync::{Arc, Mutex};
use std::thread;

let counter = Arc::new(Mutex::new(0));
let handles: Vec<_> = (0..4).map(|_| {
    let c = Arc::clone(&counter);
    thread::spawn(move || *c.lock().unwrap() += 1)
}).collect();
for h in handles { h.join().unwrap(); }
assert_eq!(*counter.lock().unwrap(), 4);
```

### Scoped threads — borrow stack data without `Arc`

`std::thread::scope` (stable since 1.63) guarantees all threads join at scope end, so they may borrow
non-`'static` stack data. Reserve `thread::spawn` (which requires `'static`) for threads that outlive
the current frame.

```rust
let mut data = vec![1, 2, 3];
std::thread::scope(|s| {
    s.spawn(|| println!("read {:?}", &data));
    s.spawn(|| { /* also borrow &data */ });
}); // all scoped threads joined here; `data` usable again
```

## Message passing — share memory by communicating

When a resource has a single logical owner, spawn a task/thread that owns it and communicate via
channels rather than sharing a lock.

| Channel | Use |
|---|---|
| `std::sync::mpsc` | Basic multi-producer/single-consumer (now crossbeam-backed) |
| `crossbeam-channel` | MPMC, `select!` over channels, timeouts, best perf |
| `tokio::sync::mpsc` (bounded) | Async pipelines **with backpressure** |
| `tokio::sync::oneshot` | Single request/response |
| `tokio::sync::broadcast` | Fan-out to many receivers |
| `tokio::sync::watch` | Latest-value / config updates |

Prefer **bounded** channels so a slow consumer applies backpressure to producers.

## Async model & runtime

- **A `Future` does nothing until polled/`.await`ed** — futures are *lazy*. Combine them (`join!`,
  `select!`, `FuturesUnordered`/`buffer_unordered`) to run concurrently on one task, or `spawn` them
  to run in parallel.
- **Tokio is the default runtime** in 2026. **async-std is discontinued (RUSTSEC-2025-0052)** — never
  start new projects on it; use Tokio, or **smol** for a minimal footprint.
- Enable only the Tokio features you use (`rt-multi-thread`, `macros`, `net`, `time`, `sync`,
  `io-util`, `fs`); `features = ["full"]` is convenient but heavy.
- `tokio::spawn` requires the future to be **`Send + 'static`**; use `spawn_local` on a `LocalSet`
  for `!Send` futures.

## The cardinal async rules

**Never hold a `std::sync::MutexGuard` across an `.await`.** It breaks `Send` and invites deadlocks.
Lock inside a sync method (or an explicit scope) so the guard drops before any `.await`:

```rust
struct Shared { map: std::sync::Mutex<std::collections::HashMap<u64, u64>> }
impl Shared {
    fn insert(&self, k: u64, v: u64) {         // sync method: guard never crosses .await
        self.map.lock().unwrap().insert(k, v);
    }
}
```

Use `tokio::sync::Mutex` **only** when you genuinely must hold a lock across `.await` (it's slower).

**Never run blocking or CPU-bound work on async threads** — it stalls the executor's worker. Offload:

```rust
let hash = tokio::task::spawn_blocking(move || expensive_hash(&data)).await?; // blocking I/O
let sum: u64 = data.par_iter().map(expensive).sum();                          // rayon, CPU-bound
```

## Structured concurrency

Prefer `JoinSet` / `CancellationToken` / scoped patterns so child tasks don't outlive their parent
and are cleaned up on failure — instead of fire-and-forget `tokio::spawn`.

```rust
let mut set = tokio::task::JoinSet::new();
for url in urls { set.spawn(fetch(url)); }
while let Some(res) = set.join_next().await {          // join_next is cancellation-safe
    match res {
        Ok(body) => process(body),
        Err(e)   => eprintln!("task failed: {e}"),
    }
}
```

**`select!`** races futures — first to complete wins, the rest are dropped/cancelled. Every branch
must be **cancellation-safe**: `mpsc::Receiver::recv` and `JoinSet::join_next` are; a partially-read
buffer generally is not — losing it corrupts data.

```rust
tokio::select! {
    msg = rx.recv()          => handle(msg),   // recv is cancellation-safe
    _   = shutdown.cancelled() => return,       // CancellationToken
}
```

## Data parallelism with rayon; when NOT to async

For CPU-bound data parallelism use **`rayon`**: turn `.iter()` into `.par_iter()` and it work-steals
across a thread pool. Keep rayon closures CPU-bound (no blocking I/O inside `join`).

**Don't reach for async at all** on CPU-bound or low-concurrency work — threads/`rayon` are simpler
and often faster. Async pays off for **many concurrent I/O-bound** tasks.

## MUST DO

- Use `Arc<Mutex<T>>`/`Arc<RwLock<T>>` for shared mutable state; drop the guard before any `.await`.
- Use `std::thread::scope` when threads borrow non-`'static` stack data.
- Prefer **bounded** channels and apply backpressure; use `oneshot`/`broadcast`/`watch` for the matching pattern.
- Move blocking I/O to `spawn_blocking` and CPU-bound parallelism to `rayon`.
- Use `JoinSet`/`CancellationToken` for structured concurrency; verify every `select!` branch is cancellation-safe.
- Pin Tokio to needed features only; treat async-std as end-of-life.

## MUST NOT DO

- Don't hold a `std::sync::MutexGuard` (or any non-`Send` guard) across an `.await`.
- Don't call blocking code (`std::fs`, `std::net`, `thread::sleep`, heavy CPU loops) directly in an async task.
- Don't `tokio::spawn` a `!Send` future (use `LocalSet`/`spawn_local`); don't fire-and-forget tasks that must be awaited/cancelled with the parent.
- Don't put non-cancel-safe operations (partial reads/writes) in a `select!` branch.
- Don't reach for async on CPU-bound or low-concurrency work.
- Don't `.await` sequentially in a loop when iterations are independent — use `join!`/`buffer_unordered`/`JoinSet`.
- Don't implement `Send`/`Sync` manually except for audited FFI types (and test it).

## Quick Reference

| Need | Use |
|---|---|
| Share ownership across threads | `Arc<T>` |
| Share mutable state across threads | `Arc<Mutex<T>>` / `Arc<RwLock<T>>` |
| Simple counter/flag | `AtomicUsize` / `AtomicBool` |
| Threads borrowing stack data | `std::thread::scope` |
| Single-owner + communicate | channel (`mpsc` / `crossbeam` / `tokio::sync`) |
| Backpressure | bounded channel |
| Blocking I/O in async | `tokio::task::spawn_blocking` |
| CPU-bound parallelism | `rayon` `par_iter()` |
| Manage many tasks | `tokio::task::JoinSet` |
| Race / cancel | `select!` + `CancellationToken` |
| Lock held across `.await` | `tokio::sync::Mutex` (last resort) |
