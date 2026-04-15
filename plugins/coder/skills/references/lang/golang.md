---
trigger: Go, Golang, goroutines, channels, gRPC, microservices Go, Go generics, concurrent programming, Go interfaces
when:
  language: golang
---

# Go Project Context

You are working in a Go project. Apply these practices consistently.

## Build and test commands

- `go build ./...` — build all packages
- `go test ./...` — run all tests (never test a single file directly)
- `go test -run TestName ./path/...` — run a specific test
- `go vet ./...` — static analysis (run before claiming done)

## Code style

- Run `gofmt` or `goimports` on every file you edit before finishing.
- Group imports in three blocks: stdlib → external → internal.
- Use `github.com/stretchr/testify/require` for test assertions.
- Prefer table-driven tests (`[]struct{ name string; ... }`) for multi-scenario coverage.

## Error handling

- Wrap errors with context: `fmt.Errorf("load config: %w", err)`
- Return `error` as the last return value; never panic on expected errors.
- Use `errors.Is` / `errors.As` for error inspection, not string matching.

## Naming conventions

- Test functions: `TestType_Method_Scenario` or `TestFunction_Scenario`
- Interfaces describe behaviour, not implementation (prefer `Reader` over `FileReader`).
- Acronyms stay uppercase: `ID`, `URL`, `HTTP`, `API`.
- Keep receiver names short and consistent (one or two letters matching the type).

## Iron laws (Go-specific)

- NEVER ignore errors with `_` unless the error is genuinely irrelevant.
- NEVER use `init()` for logic that can fail.
- Run `go vet ./...` before every completion claim.
