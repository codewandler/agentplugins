---
trigger: code review, review my code, review the changes, review pr
---

# Step 6: Requesting Code Review

**Trigger**: Between tasks or before finishing a development branch.

**Goal**: Catch issues early. Block on critical problems. Learn from mistakes.

## Review Checklist

### Specification Compliance
- [ ] Does the code do what the task requires?
- [ ] Are all acceptance criteria met?
- [ ] Are edge cases handled?

### Code Quality
- [ ] No obvious bugs or logic errors
- [ ] Proper error handling
- [ ] No memory leaks or resource leaks
- [ ] Appropriate abstraction level

### Maintainability
- [ ] Code follows project conventions
- [ ] Naming is clear and consistent
- [ ] No duplicate code (DRY)
- [ ] No commented-out code

### Tests
- [ ] Tests cover the new functionality
- [ ] Tests cover edge cases
- [ ] Tests are not brittle
- [ ] Build and tests pass

### Security
- [ ] No hardcoded secrets
- [ ] Input validation present
- [ ] Appropriate access controls

## Issue Severity

### Critical (Block Progress)
- Security vulnerability
- Data loss risk
- Breaking existing functionality
- Memory leak or resource exhaustion

### Major (Review Before Continue)
- Significant code duplication
- Poor error handling
- Unclear naming or logic

### Minor (Note and Fix Later)
- Style inconsistencies
- Missing comments
- Minor optimization opportunities

## Review Output Template

```
## Code Review: Task N - {Title}

### Critical Issues
None

### Major Issues
1. **[Issue]**: Description
   - Location: file:line
   - Suggestion: How to fix

### Minor Issues
1. Consider using more descriptive variable name at...

### Verification
- [x] Build passes
- [x] Tests pass
- [x] No regression in existing tests

### Recommendation
✅ Approved to proceed / ❌ Address critical issues first
```

## Self-Review First

Before requesting external review, do your own:

1. Re-read the task specification
2. Re-read your implementation
3. Run the tests
4. Look for the common mistakes:
   - Forgot to handle the error case
   - Wrong variable used
   - Off-by-one errors
   - Missing edge case

## Receiving Feedback

When reviewer identifies issues:

1. **Don't argue** — understand the feedback
2. **Ask clarifying questions** — if unclear
3. **Fix the issues** — follow TDD cycle
4. **Verify fixes** — run tests
5. **Report back** — what changed

## Anti-patterns

| Don't | Do |
|-------|-----|
| Skip self-review | Review your own code first |
| Defend bad code | Accept constructive feedback |
| Rush to finish | Take time to address issues properly |
| Ignore minor issues | They compound over time |
