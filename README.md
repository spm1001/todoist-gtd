# todoist-gtd

Todoist CLI with GTD coaching for Claude Code.

A Python CLI for Todoist that understands GTD semantics — outcomes vs actions, team priorities, weekly reviews. Designed as a Claude Code skill but works standalone too.

## Quick Start

```bash
# Clone and link as Claude skill
git clone https://github.com/spm1001/todoist-gtd ~/Repos/todoist-gtd
ln -s ~/Repos/todoist-gtd ~/.claude/skills/todoist-gtd

# Install (creates wrapper, installs deps)
cd ~/Repos/todoist-gtd
scripts/install.sh

# Set up OAuth (see "OAuth Setup" below first!)
todoist auth

# Verify setup
todoist doctor
```

## OAuth Setup

This CLI uses OAuth to access your Todoist. You need to register your own app:

1. Go to [developer.todoist.com](https://developer.todoist.com)
2. Click "Create a new app"
3. Fill in:
   - **App name:** anything (e.g., "My Claude Todoist")
   - **App service URL:** `http://localhost`
   - **OAuth redirect URL:** `http://localhost:8080/callback`
4. Copy the **Client ID** and **Client Secret**
5. Create your credentials file:

```bash
cd ~/Repos/todoist-gtd/scripts
cp client_credentials.json.template client_credentials.json
# Edit client_credentials.json with your client_id and client_secret
```

6. Run auth:

```bash
todoist auth
```

Browser opens, you authorize, done. Token stored in macOS Keychain.

### Manual Auth (SSH/headless)

If you can't open a browser automatically:

```bash
todoist auth --manual
```

Prints a URL. Open it, authorize, copy the failed redirect URL back.

## CLI Usage

```bash
# List projects
todoist projects

# Tasks in a project
todoist tasks --project "@Work"

# Filter syntax (same as Todoist app)
todoist filter "today"
todoist filter "assigned to: Alex & @waiting-for"

# Complete a task
todoist done <task-id>

# Add a task
todoist add "Review proposal" --project "@Work" --section "Now"

# Utility commands
todoist doctor   # Check setup and diagnose issues
todoist version  # Show version and commit info
```

## As a Claude Code Skill

When installed, Claude gains:
- **GTD vocabulary** — outcomes, areas, waiting-fors
- **Structure awareness** — outcomes as sections, 3-tier ontology
- **Weekly review support** — stale outcomes, overcommitment patterns
- **Outcome coaching** — activity language vs achievement language

Claude triggers this skill on phrases like:
- "check my @Claude inbox"
- "what's waiting for?"
- "is this a good outcome?"
- "weekly review"

## GTD Structure Expected

This skill assumes a specific Todoist setup:

| Concept | Todoist Implementation |
|---------|----------------------|
| **Outcomes** | Sections in "Desired Outcomes Q1" project |
| **Team Priorities** | Sections in a separate project |
| **Next Actions** | Tasks under outcome sections |
| **Waiting For** | `@Wait` project or `waiting-for` label |

Adapt the project names in SKILL.md to match your structure.

## Files

```
todoist-gtd/
├── SKILL.md              # Claude skill definition
├── README.md             # This file
├── requirements.txt      # Python dependencies
├── scripts/
│   ├── todoist.py        # Main CLI
│   ├── todoist_auth.py   # OAuth flow
│   ├── todoist_secrets.py # Keychain integration
│   └── client_credentials.json.template
└── references/
    ├── TERMINOLOGY.md    # GTD vocabulary
    ├── PATTERNS.md       # Query patterns
    └── COACHING.md       # Outcome quality examples
```

## Troubleshooting

### Auth Failures

**"OAuth not configured"**
- Missing `client_credentials.json`. Create it from the template with your Todoist app credentials.

**"Port 8080 is in use"**
- Another process is using port 8080, needed for OAuth callback.
- Fix: Free the port (`lsof -i :8080` to find it) or use `todoist auth --manual`.

**"Token revoked or expired"**
- Re-run `todoist auth` to re-authenticate.

**"Keychain is locked"**
- Unlock your macOS Keychain (Keychain Access app or `security unlock-keychain`).
- Or use `TODOIST_API_KEY` environment variable instead.

**"Keychain access denied"**
- Terminal needs Keychain access. Check System Preferences > Privacy > Keychain.

### Network Errors

**"Request timed out"**
- Slow connection or Todoist API issues. Retry in a moment.

**"Could not connect to Todoist"**
- Check your network connection.

### CLI Errors

**"Task not found or invalid"**
- Task ID doesn't exist or is malformed. Copy the full ID from Todoist.

**"Cannot move task between workspaces"**
- Todoist doesn't allow moving tasks between personal and team workspaces.
- Workaround: Complete the task and recreate it in the target project.

**"Rate limited by Todoist"**
- Too many requests. Wait a moment and retry.

## Security

- **Tokens** stored in macOS Keychain (not in files)
- **Client credentials** in local file (gitignored) — you register your own app
- No secrets in this repo

## License

MIT
