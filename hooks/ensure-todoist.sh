#!/bin/bash
# SessionStart hook: ensure todoist CLI is available
# Silent when everything is fine; helpful when it's not.

# Ensure ~/.local/bin is in PATH (where uv tool install puts binaries)
export PATH="$HOME/.local/bin:$PATH"

# Check if todoist CLI is available
if command -v todoist &>/dev/null; then
    exit 0
fi

# todoist not found — check if we can install it from the plugin
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-}"
if [ -n "$PLUGIN_ROOT" ] && [ -f "$PLUGIN_ROOT/pyproject.toml" ]; then
    INSTALL_HINT="uv tool install \"$PLUGIN_ROOT\""
else
    INSTALL_HINT="uv tool install todoist-gtd"
fi

cat <<EOF
{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "⚠️ todoist CLI not found. Install it:\n\n  $INSTALL_HINT\n\nThen ensure ~/.local/bin is in your PATH."}}
EOF
