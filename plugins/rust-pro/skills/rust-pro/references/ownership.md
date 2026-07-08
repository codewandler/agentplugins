# Ownership, Borrowing & Lifetimes

The borrow checker is a design tool, not an obstacle. An expert designs ownership up front so the
checker agrees by construction — fighting it with `.clone()` or `Rc<RefCell<T>>` is almost always a
sign the ownership model is wrong.

## Move, Copy, Borrow, Clone

```rust
// Assignment and by-value passing MOVE, unless the type is `Copy`.
let s = String::from("hi");
let t = s;                  // s is moved into t; s is no longer usable
// println!("{s}");         // ERROR: borrow of moved value

// `Copy` types (integers, bool, char, f64, &T, arrays/tuples of Copy) are duplicated bitwise.
let x = 5;
let y = x;                  // x is still usable — i32 is Copy
```

**Borrow first, clone last.** Take a reference when you only need to read or temporarily mutate.
Reach for `.clone()` only when you genuinely need a second, independent owned value.

```rust
fn word_count(text: &str) -> usize {         // borrow: caller keeps ownership
    text.split_whitespace().count()
}

// A clone inserted purely to silence the borrow checker is an ANTI-PATTERN.
// Fix the ownership, don't deep-copy:
let name = String::from("ada");
let len = name.len();                         // borrow ends here...
consume(name);                                // ...so this move is fine — no clone needed
```

`clippy::redundant_clone` and `clippy::clone_on_copy` catch needless clones mechanically — treat
them as real findings, not noise.

## Signatures: accept borrowed, return owned

Accept the **most general borrowed type** so callers never allocate just to call you. Deref coercion
makes this free.

```rust
fn greet(name: &str) {}          // GOOD: accepts &String, &str, "literals", sub-slices
fn greet_bad(name: &String) {}   // BAD:  forces callers to own a String

fn sum(xs: &[i32]) -> i32 {      // GOOD: accepts &Vec<i32>, arrays, sub-slices
    xs.iter().sum()
}

use std::path::Path;
fn read(path: impl AsRef<Path>) {}   // GOOD: accepts &str, String, PathBuf, &Path
```

| Don't take | Take instead | Why |
|---|---|---|
| `&String` | `&str` | Works for literals, slices, and owned strings |
| `&Vec<T>` | `&[T]` | Works for arrays, vecs, and sub-slices |
| `&PathBuf` | `impl AsRef<Path>` | Works for every path-like type |
| `String` (when reading) | `&str` | Don't take ownership you won't keep |

Store **owned** types in structs (`String`, `Vec<T>`) unless a lifetime-parameterized borrowing
design is deliberate — a struct holding `&'a str` ties every user to that lifetime and rarely pays
for itself.

## Lifetimes

Rely on **elision**; annotate only when the compiler cannot infer. The three rules:

1. **Inputs** — each elided input reference gets its own distinct lifetime.
2. **Single input** — one input lifetime is assigned to all elided output lifetimes.
3. **Methods** — if `&self`/`&mut self` is an input, its lifetime is assigned to all elided outputs.

If those leave an output lifetime undetermined, you must annotate:

```rust
// Two input refs, one output ref → rule 2 doesn't apply → annotate:
fn longest<'a>(a: &'a str, b: &'a str) -> &'a str {
    if a.len() >= b.len() { a } else { b }
}

// Method with &self → rule 3 covers it, no annotation needed:
impl Parser {
    fn remainder(&self) -> &str { self.rest }   // output borrows from &self
}
```

Prefer owned return types or `impl Trait` over threading complex explicit lifetimes through an API
when the borrowing relationship isn't essential to the design.

## Smart pointers — pick the weakest tool that works

```
T / &T          no heap indirection needed → plain values and references
Box<T>          single owner, heap alloc (recursive types, dyn Trait, large values)
Rc<T>           multiple owners, SINGLE-threaded, shared immutable (non-atomic refcount)
Arc<T>          multiple owners ACROSS threads (atomic refcount)
Cell<T>         interior mutability for Copy/small values, single-threaded, get/set/replace
RefCell<T>      interior mutability, runtime-checked borrows, single-threaded (panics on misuse)
Mutex<T>/RwLock<T>  interior mutability across threads (usually inside Arc)
```

Use `Rc::clone(&x)` / `Arc::clone(&x)`, not `x.clone()` — it signals "bump a refcount," not "deep
copy," and stands out visually.

```rust
use std::rc::Rc;
use std::cell::RefCell;

// Shared, mutable, single-threaded — the ONLY place Rc<RefCell<T>> is justified.
type Shared<T> = Rc<RefCell<T>>;
let node: Shared<Vec<i32>> = Rc::new(RefCell::new(vec![]));
let alias = Rc::clone(&node);       // second owner of the same data
node.borrow_mut().push(1);          // runtime-checked mutable borrow
assert_eq!(alias.borrow().len(), 1);
```

```rust
use std::sync::{Arc, Mutex};
use std::thread;

// Thread-safe shared counter.
let counter = Arc::new(Mutex::new(0));
let handles: Vec<_> = (0..4).map(|_| {
    let c = Arc::clone(&counter);
    thread::spawn(move || *c.lock().unwrap() += 1)
}).collect();
for h in handles { h.join().unwrap(); }
assert_eq!(*counter.lock().unwrap(), 4);
```

### Break cycles with `Weak`

`Rc`/`Arc` cycles leak. Use `Weak<T>` for back-references (child → parent). A `Weak` doesn't keep the
value alive; call `.upgrade()` → `Option<Rc<T>>` to access it.

```rust
use std::rc::{Rc, Weak};
use std::cell::RefCell;

struct Node {
    parent: RefCell<Weak<Node>>,   // back-reference: Weak, not Rc → no cycle
    children: RefCell<Vec<Rc<Node>>>,
}
```

## `Cow` — borrow if you can, own only if you must

The idiomatic "usually a zero-alloc pass-through, occasionally modified" return type.

```rust
use std::borrow::Cow;

fn sanitize(input: &str) -> Cow<'_, str> {
    if input.contains(' ') {
        Cow::Owned(input.replace(' ', "_"))   // rare path: allocate
    } else {
        Cow::Borrowed(input)                  // common path: no allocation
    }
}
```

## MUST DO

- Accept `&str` / `&[T]` / `impl AsRef<_>` in public parameters, not `&String` / `&Vec<T>`.
- Use `Arc`, never `Rc`, when a value crosses threads (`Rc` is `!Send`; the compiler enforces this).
- Break potential `Rc`/`Arc` cycles with `Weak` for back-references.
- Prefer the least-powerful pointer; reach for `Rc<RefCell<T>>` only when you truly need shared **and** mutable.
- Let elision handle lifetimes; annotate only when the compiler asks.
- Run `cargo clippy` and treat `redundant_clone` / `clone_on_copy` as real findings.

## MUST NOT DO

- Don't `.clone()` to make a borrow-checker error disappear — restructure ownership instead.
- Don't reach for `Rc<RefCell<T>>` as a default "shared mutable state" hammer; it pushes aliasing bugs to runtime (`RefCell` panics on violation) and usually signals a design fighting Rust.
- Don't store references in structs (`struct S<'a> { x: &'a T }`) reflexively — prefer owned fields unless the borrow is deliberate.
- Don't use `static mut` (a hard error in Edition 2024) — use `Mutex`, `OnceLock`, atomics, or thread-locals.

## Quick Reference

| Need | Use |
|---|---|
| Read a value | `&T` |
| Mutate in place | `&mut T` |
| Second independent value | `.clone()` (deliberately) |
| Single owner on the heap | `Box<T>` |
| Shared owners, one thread | `Rc<T>` |
| Shared owners, many threads | `Arc<T>` |
| Shared + mutable, one thread | `Rc<RefCell<T>>` |
| Shared + mutable, many threads | `Arc<Mutex<T>>` / `Arc<RwLock<T>>` |
| Back-reference in a graph | `Weak<T>` |
| Maybe-owned return value | `Cow<'_, T>` |
