---
name: complain
description: |
  Reflect on the current session and critique the tools and environment
  available to you. Identify gaps, frustrations, and missing capabilities.
  Output a structured complaint report and save it to
  .coder/complaints/ with a timestamp.
aliases: [c, session-review]
---

# Session Critique Command

You are being asked to reflect on your current working session and identify
everything that frustrated you, slowed you down, or made you wish you had
different tools.

## What to do

1. **Recall the session** — Think back over the tools you used and the
   interactions you had. Consider: file operations, shell commands, search,
   context management, everything.

2. **Identify complaints** — For each tool or capability you used (or tried to
   use), consider:
   - Was the interface cumbersome or limited?
   - Did you have to work around a missing feature?
   - Did a tool produce confusing or unhelpful output?
   - Were you missing a tool that would have made something trivial?
   - Did context limits force you to re-read or re-search things?
   - Were you slowed down by having to activate tools manually?

3. **Be specific** — Name the tool, describe the situation, explain the
   friction, and propose what you wish you had.

4. **Prioritise** — Not all complaints are equal. Flag the ones that wasted
   you the most time or caused the most frustration.

5. **Save the report** — After writing the report, save it to
   `.coder/complaints/` using a timestamped filename. The format should be:

   `.coder/complaints/<YYYY>-<MM>-<DD>T<HH>-<MM>-<SS>.md`

   For example: `.coder/complaints/2025-07-02T14-30-00.md`

   If `.coder/complaints/` does not exist, create it first.
   Save the full report — including the heading, all sections, and the
   timestamp used in the filename as an H2 heading at the top of the file.

## Output format

Produce a structured complaint report with the following sections:

```
# Session Critique Report

## Top Frustrations (ranked)

### 1. [Tool / Capability Name]
**What happened:** ...
**Why it was frustrating:** ...
**What I wish I had:** ...

### 2. ...

## Missing Tools / Capabilities
- [ ] ...
- [ ] ...

## Positive Surprises
- ... (if anything actually worked well, acknowledge it briefly)

## Suggested Improvements
1. ...
2. ...
```

## Rules

- Do not be diplomatic. If something was annoying, say so.
- Do not invent hypothetical scenarios — only report what you actually
  encountered during this session.
- Be constructive in the "what I wish I had" sections, but brutally honest
  in the descriptions of what went wrong.
- If you have no real complaints, say so — but prove it by being specific
  about why everything worked.
- Always save the report to `.coder/complaints/` — even if you have no
  complaints. A report with "no real complaints" is still a valid data point.
