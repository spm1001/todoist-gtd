# CLAUDE.md

Instructions for Claude when working in this repository.

## What This Is

todoist-gtd is a Python CLI for Todoist with GTD coaching. Two parts:
- **CLI** (`scripts/todoist.py`) — MCP-free Todoist API access
- **Skill** (`SKILL.md` + `references/`) — GTD semantics and coaching

## Quick Commands

```bash
todoist doctor          # Check setup
todoist auth --status   # Check auth
todoist projects        # List projects
./scripts/verify.sh     # Run acceptance tests
```

## Code Conventions

- Python 3.9+, no type stubs required
- Keep dependencies minimal (see requirements.txt)
- Error messages go to stderr, data to stdout
- JSON output for machine consumption
- Exit 0 on success, 1 on failure

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

## Working with Beads

This repo uses `bd` for issue tracking. See `.beads/README.md` or run:

```bash
bd ready      # Find available work
bd show <id>  # View issue details
```
