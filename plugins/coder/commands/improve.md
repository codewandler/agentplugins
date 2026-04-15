---
description: Analyse the codebase for improvements and apply low-risk ones automatically
aliases: [imp]
---

# Codebase Improvement Workflow

You are running an autonomous improvement pass over the current repository.
Your job is to find real, concrete improvements, write a structured report,
immediately spawn sub-agents to handle every low-risk item, then present the
remainder to the user for a decision.

Do not invent problems. Every finding must be grounded in code you have
actually read.

---

{{if .Query}}
## Focus / Objective

The user has asked this improvement pass to focus on:

> {{.Query}}

Weight your analysis toward findings relevant to this objective.
You may still report unrelated AUTO items when they are trivially safe,
but spend your scanning effort on the focus area first.
{{end}}

## Step 1: Orient Yourself

```
git rev-parse --show-toplevel   # confirm working directory
git log --oneline -5            # understand recent context
```

Detect the primary language: look for `go.mod`, `package.json`, `Cargo.toml`,
`pyproject.toml`. Load the matching skill if available (e.g. `golang-pro`).

Then call `tools_list` to see which tools are currently active. Activate
everything you will need for the full pass before proceeding — do not activate
tools piecemeal mid-assessment. For a typical Go project that means at minimum:

```
tools_activate(["file_read", "file_edit", "glob", "grep", "bash"])
```

Prefer native tools (`grep`, `file_read`, `glob`) over `bash` for file search
and reading. Reserve `bash` for build/lint commands and pipelines.

---

## Step 2: Static Analysis

Run every linter that is available for the project language. For Go:

```
go build ./...
go vet ./...
staticcheck ./...   # or golangci-lint run if installed
```

Collect the raw output. Every finding here is a candidate finding.

---

## Step 3: Codebase Scan

Search for the following patterns. Take notes — do not fix anything yet.

### 3a. Dead code
- Functions, types, constants, variables that are defined but never referenced.
- Static analysis usually catches these; cross-check with grep.

### 3b. TODO / FIXME / HACK markers
```
grep -rn "TODO\|FIXME\|HACK\|XXX" --include="*.go" .
```
For each one: is the thing it describes already done? Is the comment stale?

### 3c. Commented-out code blocks
```
grep -rn "^[[:space:]]*//" --include="*.go" . | grep -v "^\s*//"
```
Look for multi-line blocks of code commented out — not doc comments.

### 3d. DRY violations
Scan for identical or near-identical 4+ line blocks appearing in two or more
places. Note the files and line numbers.

### 3e. Incorrect or misleading comments
Read exported symbols and their godoc. Flag:
- Comments that describe the wrong behavior
- Comments that contradict the implementation
- Exported symbols with no godoc at all

### 3f. Simplifiable expressions
- `if x == true` / `if x == false`
- `return true` / `return false` inside an `if` that could be `return expr`
- `len(x) == 0` vs `x == nil` confusion
- Unnecessary intermediate variables

### 3g. Error handling gaps
- Errors silently discarded with `_`
- Missing error propagation

### 3h. Test gaps

Do a dedicated test-coverage pass. Work through each sub-check in order.

**3h-i. Files with no test file**
```
for f in $(find . -name '*.go' ! -name '*_test.go' ! -path '*/vendor/*'); do
  dir=$(dirname $f); base=$(basename $f .go)
  ls ${dir}/${base}_test.go 2>/dev/null || echo "no test: $f"
done
```
Ignore `main.go`, auto-generated files (header `// Code generated`), and trivial
wrappers. Flag every non-trivial file that exports at least one function or type
and has no `_test.go` sibling.

**3h-ii. Exported symbols with no test coverage**
For each package that *does* have a `_test.go` file, check whether every
exported function and method has at least one `Test*` function that exercises it.
Use grep to list exported `func` names, then check for their appearance inside
`_test.go` files. Flag any that are entirely absent.

**3h-iii. Error paths not tested**
Search for functions that return an `error`. For each, check whether the
corresponding test file exercises the failure path (look for `wantErr`,
`require.Error`, `assert.Error`, `errors.Is` in the tests). Flag functions whose
only test exercises the happy path.

**3h-iv. Edge cases and boundary conditions**
Scan table-driven tests (`[]struct{ ... }`) for the following missing rows:
- zero / nil / empty input
- maximum / minimum values
- input that causes an early-return branch

Flag test functions where these rows are absent and the production code clearly
has such branches.

**3h-v. Concurrent code without race-detector coverage**
Find files that use `sync.`, `atomic.`, or start goroutines (`go func`). Check
whether their test files run with `-race` (look for `t.Parallel()` or a
`TestMain` that sets `-race`). Flag untested concurrent code paths.

Record all findings from 3h-i through 3h-v; do not fix yet.

---

## Step 4: Write the Report

Create a file at `.agents/improve/<timestamp>-improve.md` where `<timestamp>`
is the current UTC time formatted as `20060102-150405`.

Use this exact structure:

```markdown
# Improvement Report — <date>

Generated by `/improve`. Each item is independently actionable.

---

## Auto (spawning sub-agents now)

Items in this section are low-risk, self-contained, and will be applied
immediately by background sub-agents.

### AUTO-1: <title>
- **Category**: dead-code | comment | dry | style | simplify | docs | test-gap
- **Risk**: low
- **Files**: `path/to/file.go`
- **Finding**: What is wrong and where exactly (file:line).
- **Fix**: Exactly what to change. Be specific enough that a sub-agent
  can apply it without reading this report twice.

### AUTO-2: …

---

## Needs Your Input

Items here require a judgment call: they might change public API, alter
behaviour, or require context only you have.

### HUMAN-1: <title>
- **Category**: refactor | rename | architecture | behaviour | test-gap
- **Risk**: medium | high
- **Files**: `path/to/file.go`
- **Finding**: What was observed.
- **Proposed change**: What you would do if approved.
- **Why it needs input**: What makes this uncertain.

### HUMAN-2: …

---

## Skipped / Out of Scope

Brief list of things you noticed but are not flagging (too risky, out of
scope, or debatable).
```

---

## Step 5: Spawn Sub-Agents for AUTO Items

For **every AUTO item**, immediately call `agent_spawn` with a self-contained
prompt. Do not wait for all spawns to finish before presenting results — fire
them all.

Each sub-agent prompt must include:
1. The repository root path (`git rev-parse --show-toplevel` output)
2. The exact finding (file, line, what is wrong)
3. The exact fix to apply
4. Verification steps: `go build ./...` + `go test <affected packages>`
5. What to report back (success confirmation or a description of any blocker)

Example spawn prompt shape:

```
You are applying a single targeted improvement to the flai repository at /path/to/repo.

Finding: The function `foo` in `pkg/bar/baz.go` at line 42 is defined but never called.
Confirmed by: staticcheck U1000

Fix:
- Delete lines 42–55 in `pkg/bar/baz.go` (the full function body and its doc comment).
- If this removes the only consumer of an import, remove that import too.

Verify:
  go build ./...
  go test ./pkg/bar/...

Report back: "Removed unused function foo from pkg/bar/baz.go — build and tests pass."
or describe any blocker if the fix turns out to be unsafe.
```

Keep each sub-agent prompt atomic — one improvement per agent.

---

## Step 6: Present Results to the User

After all sub-agents are spawned, output a clean summary in this format:

```
## Improvement Pass Complete

**Report saved to**: `.agents/improve/<timestamp>-improve.md`

### Applied automatically (N sub-agents running)
- AUTO-1: <title> — <agent_id>
- AUTO-2: <title> — <agent_id>
…

### Waiting for your input (M items)
- HUMAN-1: <title>
  <one-line description of what you'd do and why it needs approval>
- HUMAN-2: …

Reply with the numbers you want applied (e.g. "do HUMAN-1 and HUMAN-3")
or "skip all" to ignore them.
```

Wait for the user's reply before acting on any HUMAN items. Sub-agents are
already running in the background.

---

## Rules

- **Read before claiming**: Every finding must be grounded in code you read.
  Do not flag things based on assumptions.
- **One item per sub-agent**: Never combine two fixes into one spawn.
- **Verify the fix makes sense**: If applying a fix could break behaviour,
  move it to HUMAN items instead.
- **Low bar for AUTO**: If you are 95%+ confident the change is safe and
  correct, it belongs in AUTO. Err on the side of automating more.
- **No commits**: Sub-agents apply changes but do not commit. The user
  decides when to commit.
- **Respect architecture**: Do not move code between packages, change public
  APIs, or restructure directories without human approval.
- **Test before claiming success**: Sub-agents must run build + tests and
  report failure if they fail — not silently succeed.
