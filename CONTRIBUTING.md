# Contributing to todoist-gtd

This project welcomes contributions. Most contributors will be using Claude or similar AI assistants — these guidelines are optimized for that workflow.

## Quick Start

```bash
# Clone and set up
git clone https://github.com/spm1001/todoist-gtd.git
cd todoist-gtd
./scripts/install.sh

# Verify setup
todoist doctor
./scripts/verify.sh
```

## How to Contribute

### Reporting Bugs

Use the bug report template. Key requirements:

1. **Minimum reproduction** — Smallest steps that show the problem. Not your full workflow, just what triggers the bug.
2. **Version info** — Output of `todoist version`
3. **Expected vs actual** — What should happen, what happens instead

### Suggesting Features

Use the feature request template. Include:

1. **Problem statement** — What's frustrating or missing?
2. **Proposed solution** — Specific enough to evaluate
3. **Alternatives** — What else could work?

### Submitting PRs

1. **One change per PR** — Don't bundle unrelated fixes
2. **Run tests** — `./scripts/verify.sh` must pass
3. **Describe why** — The PR template asks for motivation, not just mechanics
4. **Update CHANGELOG** — For user-visible changes

## Code Style

- Python 3.9+
- Minimal dependencies
- Errors to stderr, data to stdout
- JSON output for machine consumption
- Exit codes: 0 success, 1 failure

## Project Structure

```
scripts/
  todoist.py          # Main CLI
  todoist_auth.py     # OAuth flow
  todoist_secrets.py  # Token storage
  verify.sh           # Acceptance tests
  install.sh          # Setup script

references/           # Skill reference docs
  COACHING.md         # GTD coaching patterns
  PATTERNS.md         # Weekly review patterns
  TERMINOLOGY.md      # GTD vocabulary

SKILL.md              # Skill definition (loads into Claude)
CLAUDE.md             # Repo instructions (Claude reads at session start)
```

## For Claude-as-Contributor

When contributing via Claude:

1. **Read CLAUDE.md first** — It has repo-specific conventions
2. **Check existing issues** — `bd ready` shows open work
3. **Small PRs** — Easier to review, faster to merge
4. **Don't guess** — If requirements are unclear, ask via issue first

### Common Mistakes

| Mistake | Fix |
|---------|-----|
| PR does multiple things | Split into focused PRs |
| No reproduction steps | Add minimum repro |
| "Fixed bug" commit message | Describe what and why |
| New dependency without justification | Explain why it's needed |
| Changes without testing | Run verify.sh |

## Issue Tracking

This repo uses `bd` (beads) for issue tracking:

```bash
bd ready              # Find unblocked work
bd show <id>          # View issue details
bd update <id> --status in_progress  # Claim work
bd close <id> --reason "..."         # Complete work
```

Issues live in `.beads/issues.jsonl` and sync with git.

## Questions?

Open an issue with the question label, or check existing issues first.
