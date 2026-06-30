# codewandler/agentplugins

A **Claude Code plugin marketplace** from codewandler. Add it once, then install any plugin below into
your global plugin store and reuse it across every project.

```
/plugin marketplace add codewandler/agentplugins
/plugin install <plugin>@agentplugins
```

Plugins install into user scope (`~/.claude/plugins/`), so they're available in all your projects.
The marketplace manifest is [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json).

## Plugins

### track — spec-driven backlog

A four-layer, in-repo tracking framework — **vision → roadmap → stories → designs** — where every
unit of work is a markdown story and the status **board** is generated **deterministically** from
story frontmatter. Slash commands cover the full story lifecycle; a self-orienting skill teaches any
agent to read the board and pick up the next ready story. Modeled on the system the
[`flux`](https://github.com/codewandler/flux) project uses, packaged for reuse anywhere.

```
/plugin install track@agentplugins
```

Then in any repo: `/track:init` to scaffold, `/track:story` / `/track:epic` to add work,
`/track:board` to sync, `/track:next` to pick up the next story. See
[`plugins/track/README.md`](plugins/track/README.md) for the full guide.

For team-wide auto-install, declare it in a repo's `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "agentplugins": { "source": { "source": "github", "repo": "codewandler/agentplugins" } }
  },
  "enabledPlugins": { "track": true }
}
```

### coder *(reference material — not yet a Claude Code plugin)*

`plugins/coder/` holds skill, command, and reference definitions for a terminal software-engineering
agent, extracted from `flai`. It predates this repo's adoption of the Claude Code plugin format (no
`plugin.json`; flai-style frontmatter) and is **not** registered in the marketplace yet — it remains
as reference content pending conversion.

## Repository layout

```
.claude-plugin/marketplace.json   # the marketplace manifest
plugins/
  track/                          # the spec-driven backlog plugin (installable)
    .claude-plugin/plugin.json
    commands/  skills/  agents/  scripts/  templates/
  coder/                          # legacy reference content (not registered)
```

## Developing

Validate a plugin or the marketplace before pushing:

```
claude plugin validate ./plugins/track --strict
claude plugin validate .                          # the marketplace manifest
```

## License

MIT
