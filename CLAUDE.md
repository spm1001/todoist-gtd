# CLAUDE.md

Instructions for Claude when working in this repository.

## What This Is

todoist-gtd is a Python CLI for Todoist with GTD coaching. Two parts:
- **CLI** (`todoist_gtd/`) — MCP-free Todoist API access, installed via `uv tool install`
- **Skill** (`SKILL.md` + `references/`) — GTD semantics and coaching

## Quick Commands

```bash
todoist doctor          # Check setup
todoist auth --status   # Check auth
todoist projects        # List projects
todoist version         # Show version
./scripts/verify.sh    # Run acceptance tests
```

## Code Conventions

- Python 3.9+, no type stubs required
- Keep dependencies minimal (see pyproject.toml)
- Error messages go to stderr, data to stdout
- JSON output for machine consumption
- Exit 0 on success, 1 on failure

## Package Structure

```
todoist_gtd/
├── cli.py          # Main CLI entry point (todoist command)
├── common.py       # Shared utilities (API client, pagination, resolution)
├── auth.py         # OAuth authentication flow
├── token_store.py  # Portable secrets management (env, keychain, file)
└── flatten.py      # Subtask flattening tool (todoist-flatten command)
```

Entry points defined in `pyproject.toml`:
- `todoist` → `todoist_gtd.cli:main`
- `todoist-flatten` → `todoist_gtd.flatten:main`

Install: `uv tool install ~/Repos/todoist-gtd`
Reinstall after changes: `uv tool install --force ~/Repos/todoist-gtd`

## Contributing

**Before filing issues or PRs, read CONTRIBUTING.md.**

Quick checklist for Claude-as-contributor:

### Issues
- Include minimum reproduction (smallest steps that show the problem)
- Include `todoist version` output
- Expected vs actual behavior
- One issue per problem

### Pull Requests
- One focused change per PR
- Run `./scripts/verify.sh` before submitting
- Describe *why*, not just *what*
- Update CHANGELOG.md for user-visible changes

### What's In Scope
- Bug fixes
- CLI improvements (new flags, better errors)
- Skill enhancements (better coaching, new patterns)
- Documentation improvements

### What's Out of Scope
- Major architectural changes (discuss first)
- New dependencies without justification
- Features that require Todoist Premium

## Working with Arc

This repo uses `arc` for issue tracking:

```bash
arc list              # See all work
arc list --ready      # Find available work
arc show <id>         # View item details
```
