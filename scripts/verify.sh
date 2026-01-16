#!/bin/bash
#
# Verification script for todoist-gtd CLI
#
# Tests key acceptance criteria from beads:
#   - auth --status works
#   - --project Personal resolution works
#   - Invalid task ID returns proper error
#
# Exit: 0 on all pass, 1 on any failure
#

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TODOIST="$SCRIPT_DIR/todoist.py"
PYTHON="${PYTHON:-$HOME/.claude/.venv/bin/python}"

passed=0
failed=0

# Color output (if terminal supports it)
if [ -t 1 ]; then
    GREEN='\033[0;32m'
    RED='\033[0;31m'
    NC='\033[0m'
else
    GREEN=''
    RED=''
    NC=''
fi

pass() {
    echo -e "  ${GREEN}✓${NC} $1"
    ((passed++))
}

fail() {
    echo -e "  ${RED}✗${NC} $1"
    if [ -n "${2:-}" ]; then
        echo "    → $2"
    fi
    ((failed++))
}

run_cmd() {
    "$PYTHON" "$TODOIST" "$@" 2>&1
}

echo "Verifying todoist-gtd CLI..."
echo

# Test 1: auth --status
echo "[Auth]"
output=$(run_cmd auth --status)
exit_code=$?
if [ $exit_code -eq 0 ]; then
    pass "auth --status (authenticated)"
else
    fail "auth --status" "Not authenticated - run 'todoist auth' first"
    echo
    echo "Cannot continue without authentication."
    exit 1
fi

# Test 2: Project resolution (--project Personal)
echo
echo "[Project Resolution]"

# First check Personal project exists
output=$(run_cmd projects)
if echo "$output" | grep -q '"name": "Personal"'; then
    pass "Personal project exists"
else
    # Try Inbox as fallback (some accounts use Inbox instead)
    if echo "$output" | grep -q '"name": "Inbox"'; then
        pass "Inbox project exists (no Personal, using Inbox)"
        TEST_PROJECT="Inbox"
    else
        fail "Personal/Inbox project not found" "Need a default project to test"
        TEST_PROJECT=""
    fi
fi
TEST_PROJECT="${TEST_PROJECT:-Personal}"

# Test --project resolution
if [ -n "$TEST_PROJECT" ]; then
    output=$(run_cmd tasks --project "$TEST_PROJECT" 2>&1)
    exit_code=$?
    if [ $exit_code -eq 0 ]; then
        pass "--project $TEST_PROJECT resolution works"
    else
        fail "--project $TEST_PROJECT resolution" "$output"
    fi
fi

# Test 3: Invalid task ID error handling
echo
echo "[Error Handling]"

# Use a clearly invalid task ID
output=$(run_cmd task "invalid-task-id-12345" 2>&1)
exit_code=$?
if [ $exit_code -ne 0 ]; then
    if echo "$output" | grep -qi "not found\|invalid"; then
        pass "Invalid task ID returns error with message"
    else
        fail "Invalid task ID returns error but message unclear" "$output"
    fi
else
    fail "Invalid task ID should return non-zero exit" "Got exit 0"
fi

# Test 4: Sections require project context
output=$(run_cmd sections --project "$TEST_PROJECT" 2>&1)
exit_code=$?
if [ $exit_code -eq 0 ]; then
    pass "sections --project works"
else
    fail "sections --project failed" "$output"
fi

# Summary
echo
echo "────────────────────────────────────────"
total=$((passed + failed))
if [ $failed -eq 0 ]; then
    echo -e "${GREEN}All $total tests passed.${NC}"
    exit 0
else
    echo -e "${RED}$passed/$total tests passed, $failed failed.${NC}"
    exit 1
fi
