#!/bin/bash
#
# Install script for todoist-gtd CLI
#
# Creates wrapper script, installs dependencies, verifies setup.
#
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
WRAPPER_DIR="$HOME/.claude/scripts"
WRAPPER_PATH="$WRAPPER_DIR/todoist"
VENV_PYTHON="$HOME/.claude/.venv/bin/python"

echo "Installing todoist-gtd..."
echo

# Check Python and venv
echo "[1/5] Checking Python..."

# Create venv if it doesn't exist
if [ ! -d "$HOME/.claude/.venv" ]; then
    echo "  Creating venv at ~/.claude/.venv..."
    mkdir -p "$HOME/.claude"
    if ! python3 -m venv "$HOME/.claude/.venv"; then
        echo "  ✗ Failed to create venv"
        echo "    Ensure python3 is installed with venv support"
        exit 1
    fi
    echo "  ✓ Created venv"
fi

if [ ! -x "$VENV_PYTHON" ]; then
    echo "  ✗ Python not found in venv at $VENV_PYTHON"
    exit 1
fi

PY_VERSION=$("$VENV_PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "  ✓ Found Python $PY_VERSION"

# Install dependencies
echo
echo "[2/5] Installing dependencies..."
"$VENV_PYTHON" -m pip install -q -r "$REPO_DIR/requirements.txt"
echo "  ✓ Dependencies installed"

# Create wrapper directory
echo
echo "[3/5] Creating wrapper directory..."
mkdir -p "$WRAPPER_DIR"
echo "  ✓ $WRAPPER_DIR exists"

# Create wrapper script
echo
echo "[4/5] Creating wrapper script..."

# Create/update symlink to repo (allows moving repo without breaking wrapper)
REPO_LINK="$WRAPPER_DIR/.todoist-gtd-repo"
ln -sfn "$REPO_DIR" "$REPO_LINK"

cat > "$WRAPPER_PATH" << 'WRAPPER_EOF'
#!/bin/bash
# Wrapper for todoist-gtd CLI
# Follows symlink to find repo — survives repo moves if you re-run install.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(readlink "$SCRIPT_DIR/.todoist-gtd-repo")"
VENV_PYTHON="$HOME/.claude/.venv/bin/python"
exec "$VENV_PYTHON" "$REPO_DIR/scripts/todoist.py" "$@"
WRAPPER_EOF
chmod +x "$WRAPPER_PATH"
echo "  ✓ Created $WRAPPER_PATH"
echo "  ✓ Linked to $REPO_DIR"

# Check PATH
echo
echo "[5/5] Checking PATH..."
if [[ ":$PATH:" != *":$WRAPPER_DIR:"* ]]; then
    echo "  ⚠ ~/.claude/scripts is not in PATH"
    echo
    echo "  Add this to your ~/.zshrc or ~/.bashrc:"
    echo "    export PATH=\"\$HOME/.claude/scripts:\$PATH\""
    echo
    echo "  Then run: source ~/.zshrc"
else
    echo "  ✓ PATH includes ~/.claude/scripts"
fi

# Summary
echo
echo "────────────────────────────────────────"
echo "Installation complete!"
echo
echo "Next steps:"
echo "  1. Set up OAuth credentials (see README.md)"
echo "  2. Run: todoist auth"
echo "  3. Run: todoist doctor (to verify setup)"
