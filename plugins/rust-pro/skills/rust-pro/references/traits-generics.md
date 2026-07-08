# Traits, Generics & Abstraction

Traits are Rust's core abstraction. The expert instinct: prefer **zero-cost static dispatch**
(generics, `impl Trait`) by default, drop to **dynamic dispatch** (`dyn Trait`) only for genuine
heterogeneity, and encode invariants in the type system so illegal states don't compile.

## Trait design & coherence

**The orphan rule:** you may `impl Trait for Type` only if the trait *or* the type is local to your
crate. To implement a foreign trait on a foreign type, use the **newtype pattern**:

```rust
struct Wrapper(Vec<String>);              // local type wrapping a foreign one
impl std::fmt::Display for Wrapper {      // now legal: Wrapper is local
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "[{}]", self.0.join(", "))
    }
}
```

- **Default methods** keep the required surface minimal (the `Iterator`/`Ord` model): implementers
  override only what differs.
- **Seal traits** you don't want implemented downstream — lets you add methods later without a
  breaking change (API Guidelines C-SEALED):

  ```rust
  pub trait Encoder: sealed::Sealed {
      fn encode(&self, buf: &mut Vec<u8>);
  }
  mod sealed {
      pub trait Sealed {}
      impl Sealed for super::Json {}
  }
  ```
- **Keep trait bounds off struct/enum definitions** (C-STRUCT-BOUNDS) — put them on the impls/methods
  that need them. Bounds on the type are a breaking change and usually redundant with `derive`.

## Associated types vs generic parameters

| Use | When |
|---|---|
| **Associated type** (`type Item;`) | Exactly one logical output type per implementer (`Iterator::Item`, `Deref::Target`) |
| **Generic parameter** (`Trait<T>`) | A type can implement the trait multiple ways (`From<T>`, `AsRef<T>`) |

## Generics, `impl Trait`, and dispatch

```rust
// impl Trait in ARGUMENT position = anonymous generic:
fn print(x: impl std::fmt::Display) {}       // ≡ fn print<T: Display>(x: T)

// impl Trait in RETURN position = one opaque concrete type (no boxing):
fn evens(v: &[i32]) -> impl Iterator<Item = &i32> {
    v.iter().filter(|n| *n % 2 == 0)
}
```

- **Static dispatch (generics/monomorphization)** — the default: zero-cost, inlinable; costs are code
  bloat and slower compiles.
- **Dynamic dispatch (`dyn Trait`)** — use to store heterogeneous types together, cross an API/ABI
  boundary, cut monomorphization bloat, or break recursion; costs a vtable indirection.

```rust
fn draw_all<T: Draw>(items: &[T])         { for i in items { i.draw(); } } // one T, monomorphized
fn draw_any(items: &[Box<dyn Draw>])      { for i in items { i.draw(); } } // heterogeneous, vtable
```

Prefer `&dyn Trait` / `&mut dyn Trait` for borrowed trait objects and `Box<dyn Trait>` for owned
ones. Add `+ Send + Sync + 'static` explicitly when the object crosses threads.

### dyn compatibility (formerly "object safety")

A trait is usable as `dyn Trait` only if it has **no** generic methods, **no** `Self` in return
position, **no** associated consts, **no** `Self: Sized` supertrait, and **no** bare `async fn`/RPITIT
methods. Gate non-dispatchable helpers with `where Self: Sized`. Valid receivers for dispatchable
methods: `&self`, `&mut self`, `Box<Self>`, `Rc<Self>`, `Arc<Self>`, `Pin<P>` of those.

## Conversions, newtypes, smart pointers

- Implement **`From`, not `Into`** — you get `Into` free via the blanket impl (C-CONV-TRAITS). Same
  for **`TryFrom`** → `TryInto`. Accept `impl Into<T>` in constructors for ergonomic call sites.
- Use `TryFrom`/`TryInto` for **fallible** conversions (real `Error`); `From`/`Into` only for
  **infallible** ones. **Never make `From` panic.**
- Implement **`AsRef`/`AsMut`** for cheap reference-to-reference views; accept `impl AsRef<Path>` /
  `impl AsRef<str>` in APIs.
- Implement **`Deref`/`DerefMut` only for smart-pointer types** (C-DEREF). Do **not** use `Deref` to
  fake inheritance or auto-expose a newtype's inner API — that's the "Deref polymorphism"
  anti-pattern; add explicit methods or `AsRef` instead.

```rust
impl From<u16> for Celsius { fn from(v: u16) -> Self { Celsius(v as i32) } }

impl TryFrom<i32> for NonNegative {
    type Error = OutOfRange;
    fn try_from(v: i32) -> Result<Self, Self::Error> {
        if v >= 0 { Ok(NonNegative(v)) } else { Err(OutOfRange) }
    }
}
```

## Standard traits — derive eagerly (C-COMMON-TRAITS)

The orphan rule means downstream users **cannot** add these later, so provide them where the type's
semantics allow: `Debug` (almost always), `Clone`, `Copy` (small POD only), `PartialEq`/`Eq`,
`PartialOrd`/`Ord`, `Hash`, `Default`.

- Implement **`Display`** for user-facing text — never `derive` it.
- Provide `new()` and `Default` together when a zero-arg constructor makes sense (`Default` plugs
  into `unwrap_or_default`, `*_or_default`).
- Getters are `fn field(&self)` — **no `get_` prefix** (C-GETTER); the mutable form is
  `fn field_mut(&mut self)`.

## Builder & typestate patterns

**Builder** — for types with many optional/defaulted fields (Rust has no default args). Mark it
`#[must_use]`; finish with `build(self) -> T` (or `-> Result<T, E>` if it validates):

```rust
#[must_use]
pub struct RequestBuilder { url: String, timeout: Option<u32>, retries: u32 }

impl RequestBuilder {
    pub fn new(url: impl Into<String>) -> Self {
        Self { url: url.into(), timeout: None, retries: 0 }
    }
    pub fn timeout(mut self, ms: u32) -> Self { self.timeout = Some(ms); self }
    pub fn retries(mut self, n: u32) -> Self { self.retries = n; self }
    pub fn build(self) -> Request { /* ... */ }
}
```

**Typestate** — encode state in a `PhantomData<S>` type parameter so illegal transitions don't
compile. Zero runtime cost via move semantics:

```rust
use std::marker::PhantomData;
struct Door<S>(PhantomData<S>);
struct Open; struct Closed;

impl Door<Closed> { fn open(self)  -> Door<Open>   { Door(PhantomData) } }
impl Door<Open>   { fn close(self) -> Door<Closed> { Door(PhantomData) } }
// door.open().open()  // compile error: no `open` on Door<Open>
```

## Recent trait features (stable)

- **`async fn` in traits + RPITIT** (stable since **1.75**) — use freely in application/internal
  traits. But they are **not dyn compatible**: for `dyn` async traits use `#[async_trait]` (boxes the
  future). In **public** traits, a bare `async fn` warns (no `Send` bound); generate a `Send`-bounded
  variant with `#[trait_variant::make(Trait: Send)]` for multithreaded runtimes like Tokio.
- **GATs** (generic associated types, `type Item<'a>;`, stable **1.65**) — lending iterators and
  lifetime-parameterized associated types.
- **Precise capturing** `impl Trait + use<T>` (stable **1.82**) — control which generics/lifetimes an
  RPIT return captures (important in Edition 2024, which captures everything by default).

## MUST DO

- Derive `Debug` on virtually every public type; derive the full common-trait set where semantics allow.
- Implement `From`/`TryFrom` (not `Into`/`TryInto`); implement `AsRef` for view conversions.
- Seal traits meant only for internal implementation; keep struct fields private for non-POD types.
- Prefer generics/`impl Trait` (static dispatch) by default; switch to `dyn` deliberately.
- Add explicit `Send + Sync + 'static` bounds to trait objects that cross threads.
- Use `#[trait_variant::make(_: Send)]` (or `#[async_trait]` for `dyn`) for async traits used with Tokio.

## MUST NOT DO

- Don't `impl Into`/`impl TryInto` directly, or add derive-matching bounds to struct/enum definitions.
- Don't implement `Deref`/`DerefMut` for anything that isn't a genuine smart pointer, or use it to emulate inheritance.
- Don't make a public trait `dyn`-incompatible without intent (generic methods, `Self` return, bare `async fn`) if you need `dyn`.
- Don't let `From` panic — use `TryFrom` for fallible conversions.
- Don't default to `dyn` when a generic gives zero-cost static dispatch over a known set of types.
- Don't over-abstract: no speculative trait hierarchies or one-impl traits — abstract on the second concrete need.

## Quick Reference

| Goal | Mechanism |
|---|---|
| Foreign trait on foreign type | Newtype wrapper |
| One output type per impl | Associated type |
| Multiple impls per type | Generic trait parameter `Trait<T>` |
| Zero-cost, known types | Generics / `impl Trait` (static dispatch) |
| Heterogeneous collection | `Box<dyn Trait>` (dynamic dispatch) |
| Infallible conversion | `impl From<T>` (get `Into` free) |
| Fallible conversion | `impl TryFrom<T>` |
| Cheap borrowed view | `impl AsRef<T>` |
| Many optional fields | Builder + `#[must_use]` |
| Compile-time state machine | Typestate + `PhantomData` |
| Prevent downstream impls | Sealed trait |
| Async method, static dispatch | `async fn` in trait (1.75+) |
| Async method, `dyn` | `#[async_trait]` |
