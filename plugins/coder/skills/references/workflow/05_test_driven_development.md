---
trigger: write tests, test first, tdd, unit test, add tests
---

# Step 5: Test-Driven Development (TDD)

**Trigger**: Active during implementation. Enforced for every code change.

**Goal**: Write correct, verified code by following the RED-GREEN-REFACTOR cycle.

## The RED-GREEN-REFACTOR Cycle

### RED: Write the Failing Test

```bash
# Activate tools
tools_activate("file_*", "bash", "grep")
```

1. Write a test that describes the behavior you want
2. Run it — it MUST fail
3. If it passes, your test is wrong (testing implementation, not behavior)

```go
func TestFeature_DesiredBehavior(t *testing.T) {
    // Given
    input := "test data"
    
    // When
    result, err := DoSomething(input)
    
    // Then
    require.Error(t, err)           // We expect an error for now
    require.Nil(t, result)
}
```

### GREEN: Write Minimal Implementation

1. Write ONLY the code needed to make the test pass
2. No optimization, no "what if" features
3. If a test fails, add the simplest fix

```go
func DoSomething(input string) (*Result, error) {
    return nil, ErrNotImplemented  // Simplest "working" code
}
```

### REFACTOR: Clean Up

1. Run tests — they MUST pass
2. Improve code structure (rename, extract, simplify)
3. Ensure tests still pass
4. Delete any code that isn't covered by tests

## TDD Anti-patterns

| Don't | Do |
|-------|-----|
| Write implementation first | Always RED first |
| Write tests that pass initially | Tests must fail on RED |
| Keep dead code "just in case" | Delete uncovered code |
| Skip the refactor step | Clean as you go |
| Test implementation details | Test behavior |
| Write assertions before arranging | Follow: Arrange → Act → Assert |

## Testing Anti-patterns Reference

### Naming Tests Badly
```go
// ❌ Bad
func Test1(t *testing.T) { ... }
func TestDoThing(t *testing.T) { ... }

// ✅ Good
func TestParser_Parse_ReturnsErrorOnEmptyInput(t *testing.T)
func TestAdapter_pump_TextContentAccumulated(t *testing.T)
```

### Incomplete Coverage
```go
// ❌ Bad — only tests happy path
func TestDoThing(t *testing.T) {
    result, _ := DoThing()  // Ignoring error!
    require.Equal(t, expected, result)
}

// ✅ Good — test error cases too
func TestDoThing(t *testing.T) {
    tests := []struct {
        name    string
        input   string
        wantErr bool
    }{
        {"valid input", "data", false},
        {"empty input", "", true},
        {"invalid format", "bad", true},
    }
}
```

### Brittle Tests
```go
// ❌ Bad — checks exact output including timestamp
got := DoThing()
assert.Equal(t, "Created at 2024-01-01T00:00:00Z", got.String())

// ✅ Good — checks relevant behavior
got := DoThing()
assert.Equal(t, StatusPending, got.Status())
assert.NotEmpty(t, got.ID())
```

## Running Tests

```bash
# Single test
go test -v -run TestFeature_DesiredBehavior ./...

# All tests in package
go test ./...

# With coverage
go test -cover ./...

# Watch mode (requires testwatch)
go testwatch ./...
```

## Enforcement

**Iron Law**: NO production code WITHOUT a failing test first.

If you find yourself wanting to skip TDD:
- Ask: "What prevents me from writing the test first?"
- The test documents the expected behavior — it's not extra work, it's the work.
