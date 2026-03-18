#!/bin/bash
# SessionStart hook: ensure todoist CLI and API token are available
# Silent when everything is fine; helpful when it's not.

# Ensure ~/.local/bin is in PATH (where uv tool install puts binaries)
export PATH="$HOME/.local/bin:$PATH"

ISSUES=""

# 1. Check CLI
if ! command -v todoist &>/dev/null; then
    PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-}"
    if [ -n "$PLUGIN_ROOT" ] && [ -f "$PLUGIN_ROOT/pyproject.toml" ]; then
        ISSUES="${ISSUES}• todoist CLI not found. Install: uv tool install \"$PLUGIN_ROOT\" && export PATH=\"\$HOME/.local/bin:\$PATH\"\n"
    else
        ISSUES="${ISSUES}• todoist CLI not found. Install: uv tool install todoist-gtd && export PATH=\"\$HOME/.local/bin:\$PATH\"\n"
    fi
fi

# 2. Check API token
if [ -z "${TODOIST_API_KEY:-}" ]; then
    ISSUES="${ISSUES}• No TODOIST_API_KEY set. Get your token from https://todoist.com/prefs/integrations then: export TODOIST_API_KEY=\"your_token\"\n"
fi

# If no issues, exit silently
[ -z "$ISSUES" ] && exit 0

cat <<EOF
{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "⚠️ Todoist setup needed:\n\n${ISSUES}"}}
EOF
