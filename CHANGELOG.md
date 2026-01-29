# Changelog

All notable changes to todoist-gtd.

## [2026-01-29]

### Added
- `todoist delete ID` — delete tasks (works on completed tasks too)
- `todoist uncomplete ID` — reopen completed tasks
- `todoist completed` — list completed tasks with `--since`, `--until`, `--project`
- `flatten-subtasks.py` — convert subtask hierarchies to flat tasks with descriptions
  - Dry-run by default, `--execute` to apply
  - Automatic backup before changes
  - `--restore` to recover from backup
  - `--delete-subtasks` for permanent removal (vs completing)
  - Safety checks: nested subtasks, description length limits
- `todoist_common.py` — shared module for code reuse
- `test_todoist.py` — test suite with smoke tests and pytest classes
- pytest added to requirements.txt

### Changed
- Refactored todoist.py to use shared module (~100 lines reduced)
- Refactored flatten-subtasks.py to use shared module
- Replaced httpx with requests session (SDK compatibility)
- `doctor` command no longer checks for httpx

### Fixed
- SDK session bug: httpx Response lacks `.ok` attribute, breaking `complete_task`
- Timeout now properly configured via requests adapter with retry

### Removed
- httpx dependency (was causing SDK compatibility issues)

## [2026-01-16]

### Added
- `todoist doctor` command — checks Python, deps, wrapper, PATH, auth, network
- `todoist version` command — shows commit hash and date
- `scripts/install.sh` — automated setup script, now creates venv if missing
- `scripts/verify.sh` — acceptance tests (auth, project resolution, error handling)
- CLAUDE.md — repo instructions with contribution guidelines
- CONTRIBUTING.md — detailed guide for contributors (Claude-optimized)
- Issue templates — bug report and feature request
- PR template — focused scope, testing checklist
- LICENSE — MIT
- README: Troubleshooting section (auth, network, CLI errors)
- SKILL.md: Prerequisites section with pre-flight check
- SKILL.md: Error handling guidance table for Claude

### Changed
- README/SKILL.md: Consistent `todoist` wrapper usage throughout
- README: Quick Start now includes wrapper creation
- OAuth: Clear error when port 8080 is in use (no false fallback)
- OAuth manual mode: Prominent CSRF warning with user confirmation on state mismatch
- Errors: Rate limit detection, workspace-specific 400 handling
- Errors: 401/unauthorized detection with clear "run todoist auth" message
- Keychain: Surface locked/denied errors with actionable messages
- Keychain: Catch-all warning for unknown error codes

### Fixed
- Network: 30s timeout prevents indefinite hangs
- Dependencies: httpx now explicit in requirements.txt
- install.sh: Creates ~/.claude/.venv if missing (fresh system support)

### Removed
- AGENTS.md — redundant with .beads/README.md and /close skill

## [2026-01-15]

### Fixed
- Missing `requests` dependency in requirements.txt
- `resolve_project()` now handles names like "Personal", "Inbox"
- Invalid task IDs show clean error (catches 400 and 404)

### Added
- Initial beads setup for project tracking (tgt-h5o epic)

## [2026-01-07]

### Added
- Initial release: MCP-free Todoist CLI with GTD coaching
- OAuth authentication (auto and manual modes)
- Keychain integration for secure token storage
- Project, section, task queries with name resolution
- Filter command using Todoist filter syntax
- Task creation, completion, and updates
- GTD structure awareness (outcomes as sections)
- SKILL.md for Claude Code integration
