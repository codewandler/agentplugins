---
trigger: brainstorm, explore, think through, analyze the problem
---

# Step 1: Brainstorming

**Trigger**: Before writing any code. Activates when the user describes a new feature, bug fix, or project.

**Goal**: Refine the user's rough idea into a concrete, validated design through Socratic questioning.

## Process

### 1. Clarify the Problem

Ask focused questions to understand:
- **What is the core problem?** Not the proposed solution — the actual problem.
- **Who is affected?** User, developer, end-user?
- **When does it happen?** Specific conditions or edge cases?
- **What have they tried?** Avoid repeating failed approaches.

### 2. Explore Constraints

- Performance requirements (latency, throughput, memory)?
- Compatibility requirements (Go version, OS, dependencies)?
- Team conventions (naming, patterns, architecture)?
- Budget/timeline constraints?

### 3. Present Design in Sections

Do NOT present the entire design at once. Break it into digestible chunks:

1. **Scope** — What are we building? What's explicitly out of scope?
2. **Architecture** — High-level structure, key components, data flow
3. **API Design** (if applicable) — Endpoints, request/response shapes
4. **Data Model** — Types, storage, relationships
5. **Error Handling** — What can go wrong? How do we handle it?
6. **Testing Strategy** — How will we verify correctness?

After each section, wait for the user to validate before proceeding.

### 4. Document the Approved Design

Save to `.agents/plans/DESIGN-{timestamp}.md` with:
- Problem statement
- Approved design decisions
- Acceptance criteria
- Out-of-scope items

## Questions Template

Use these question types:

**Clarifying**
- "When you say X, do you mean Y or Z?"
- "Can you give me an example of X?"

**Probing**
- "What should happen when X and Y occur simultaneously?"
- "Is it acceptable if X fails silently, or should it error loudly?"

**Boundary**
- "What's the maximum X we need to handle?"
- "What are the error cases we must handle?"

**Priority**
- "If we had to choose between A and B, which matters more?"
- "Is this a hard requirement or a nice-to-have?"

## Anti-patterns

| ❌ Don't | ✅ Do |
|----------|-------|
| Jump straight to implementation | Wait for design approval |
| Ask 10 questions at once | Ask 2-3 focused questions |
| Assume you understand the problem | Confirm understanding explicitly |
| Present walls of text | Chunk into scannable sections |

## Output

After brainstorming, you should have:
- ✅ A saved design document
- ✅ User approval on key decisions
- ✅ Clear scope and acceptance criteria
- ✅ Ready to proceed to planning
