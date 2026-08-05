---
description: Regenerate the status board through Flux, rewriting only the generated region.
argument-hint: "[repo-root]"
---

# /track:board

Regenerate `docs/stories/README.md`'s generated region from story frontmatter. `$1` is the optional
repository root (default `.`).

## Run Flux's native Track backend

```bash
flux board --root "${1:-.}" render
```

`flux board` is the supported renderer and automation API. Do not invoke a Python fallback or
recreate the renderer in prompt code.

Report the generator's summary line (and any warnings) to the user. The script:
- rewrites only the region between `<!-- BEGIN track:board -->` and `<!-- END track:board -->`,
  preserving the hand-written intro / status summary / epic narratives;
- groups stories by status (Now / Next / Blocked / Backlog) and by `epic`; lists `done` stories with
  a `CHANGELOG.md` pointer;
- parses optional `areas` metadata for query consumers but does not render it on board rows;
- is idempotent (a second run makes no change).

## If Flux is unavailable

Stop with a clear installation error. The plugin deliberately has no second mutation path: a manual
or private-script renderer would drift from the same revision/idempotency contract used by Codex,
Claude and fleet automation. `flux board skill` is the concise operating guide and
`flux board schema --output json` is the complete machine contract.

## If the markers are missing

The board has no `<!-- BEGIN track:board -->` / `<!-- END track:board -->` markers. Don't guess where
the generated region goes — tell the user to run `/track:init` (which seeds a board with the markers),
or add the two marker lines themselves where they want the generated lists.
