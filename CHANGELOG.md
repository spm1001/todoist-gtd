# Changelog

All notable changes to todoist-gtd.

## [Unreleased]

### Added
- `todoist doctor` command — checks Python, deps, wrapper, PATH, auth, network
- `todoist version` command — shows commit hash and date
- `scripts/install.sh` — automated setup script

## [2026-01-16]

### Added
- README: Troubleshooting section (auth, network, CLI errors)
- SKILL.md: Prerequisites section with pre-flight check
- SKILL.md: Error handling guidance table for Claude
- AGENTS.md: Agent instructions for bd workflow

### Changed
- README/SKILL.md: Consistent `todoist` wrapper usage throughout
- README: Quick Start now includes wrapper creation
- OAuth: Clear error when port 8080 is in use (no false fallback)
- Errors: Rate limit detection, workspace-specific 400 handling
- Keychain: Surface locked/denied errors with actionable messages
- Keychain: Catch-all warning for unknown error codes

### Fixed
- Network: 30s timeout prevents indefinite hangs
- Dependencies: httpx now explicit in requirements.txt

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
