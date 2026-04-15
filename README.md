# codewandler/agentplugins

Plugin definitions for agent systems, following Claude plugin directory layout.

## Structure

```
plugins/
└── coder/              (Coder IDE plugin)
    ├── skills/         (Agent capabilities with references)
    ├── commands/       (Slash command specifications)
    └── agents/         (Agent configurations)
```

## Plugin: Coder

The **Coder** plugin defines a terminal-based software engineering agent.

### Skills

- **coder** - Core identity and workflow (with references)
  - Language guides (Go)
  - Workflow guides (brainstorming, git, planning, etc.)
- **gitworktree** - Git worktree workflow

### Commands

- **commit** - Commit guidelines and best practices
- **release** - Release procedures
- **review** - Code review standards
- **improve** - Continuous improvement process
- **complain** - Feedback mechanism

## Usage

Each plugin can be loaded by agent systems to provide:
- Skill definitions (in SKILL.md files with YAML frontmatter)
- Command specifications
- Reference materials for agent guidance

## Status

v0.1.0 — Initial plugin definitions extracted from flai.

## License

MIT
