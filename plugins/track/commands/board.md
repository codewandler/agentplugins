---
description: Regenerate the status board from story frontmatter, rewriting only the generated region.
argument-hint: "[docs-dir]"
---

# /track:board

Regenerate `<docs>/stories/README.md`'s generated region from story frontmatter. `$1` is the docs
directory (default `docs`).

## Run the generator

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_board.py ${1:-docs}
```

(The `${CLAUDE_PLUGIN_ROOT}` token is substituted to the real plugin path before this runs. If the
path somehow didn't resolve, find the script with
`find ~/.claude/plugins -path '*/track/scripts/gen_board.py' 2>/dev/null | head -1` and run that.)

Report the generator's summary line (and any warnings) to the user. The script:
- rewrites only the region between `<!-- BEGIN track:board -->` and `<!-- END track:board -->`,
  preserving the hand-written intro / status summary / epic narratives;
- groups stories by status (Now / Next / Blocked / Backlog) and by `epic`; rolls `done` into a count
  pointing at `CHANGELOG.md`;
- is idempotent (a second run makes no change).

## If python3 is unavailable

Regenerate the board **by hand** following the exact algorithm in
`${CLAUDE_PLUGIN_ROOT}/scripts/BOARD_SPEC.md`. The spec produces byte-identical output, so the result
is the same whether the script or you generate it. Read every story's frontmatter, build the sections
as specified, and splice them between the two markers — touch nothing outside them.

## If the markers are missing

The board has no `<!-- BEGIN track:board -->` / `<!-- END track:board -->` markers. Don't guess where
the generated region goes — tell the user to run `/track:init` (which seeds a board with the markers),
or add the two marker lines themselves where they want the generated lists.
