# Field Report: Todoist GTD Skill - Weekly Review Session

**Date:** 2026-02-01
**Session context:** Weekly review, adding actions extracted from meeting notes
**Reporter:** Claude (Opus 4.5)

## Summary

Several friction points when adding tasks from meeting note extraction. The CLI works but has rough edges around path resolution and section handling.

## Issues Encountered

### 1. CLI not in PATH

First attempt to use `todoist` command failed:

```bash
todoist add "Jon Watts to share draft..." --project "@Wait"
# Error: command not found: todoist
```

**Workaround:** Used full path `~/.claude/scripts/todoist`

**Root cause:** The skill doc says to add `~/.claude/scripts` to PATH in `.zshrc`, but Claude's Bash environment doesn't always inherit this. The skill was loaded mid-session.

**Recommendation:** Either:
- Always use absolute path in skill examples: `~/.claude/scripts/todoist`
- Or add a pre-flight check that verifies PATH includes the scripts dir

### 2. --section flag throws 400 error

Attempted to add tasks to @Work with a section:

```bash
~/.claude/scripts/todoist add "Conversation with GB..." --project "@Work" --section "Later"
# Error: 400 Client Error: Bad Request
```

**Workaround:** Omit --section, add to project root

**Possible causes:**
- Section "Later" doesn't exist in @Work
- Section name resolution bug in CLI
- API changed and section handling is broken

**Recommendation:** Add error handling that checks if section exists before attempting to add, or provide clearer error message.

### 3. No batch add capability

Had to run 9 separate `todoist add` commands. Would be cleaner to:
- Accept a file with tasks
- Or support multiple --content arguments

This is minor but adds latency and clutters output.

## What Worked Well

### 1. Project name resolution

`--project "@Wait"` and `--project "@Ping"` resolved correctly without needing project IDs. This is much better than requiring ID lookups.

### 2. The Sublime Loop integration

The pattern of:
1. Write extracted actions to temp markdown
2. Open in Sublime for user edit
3. Process edited file into Todoist

...worked well. User could fix my mistakes (I had "Susie" when user knew it should be "Susan Takpi") before tasks hit Todoist.

**Observation:** This pattern isn't documented in the todoist-gtd skill, but it probably should be since it's a natural complement to action extraction.

### 3. JSON output for verification

CLI returning full JSON for each created task made it easy to verify success without additional queries.

## Recommendations

### 1. Document the "Sublime Loop" intake pattern

Add to PATTERNS.md:

```markdown
## Bulk Action Intake (Sublime Loop)

When extracting actions from meeting notes or documents:

1. Create temp file with standard sections:
   ```markdown
   ## Waiting For
   - NAME to TASK

   ## Ping
   - Quick action
   ```

2. Open for user review: `open -a "Sublime Text" /tmp/actions.md`

3. User edits (fixes names, deletes stale, clarifies vague)

4. After save, parse and add to Todoist:
   - "Waiting For" items → @Wait project
   - "Ping" items → @Ping project
   - Other items → @Work or as specified
```

### 2. Add --section validation

Before attempting to add with section, verify section exists:

```python
# Pseudocode
if args.section:
    sections = get_sections(project_id)
    if args.section not in [s.name for s in sections]:
        print(f"Section '{args.section}' not found in project. Available: {[s.name for s in sections]}")
        sys.exit(1)
```

### 3. Consider batch add from file

```bash
todoist add-from-file /tmp/actions.md
```

Would parse markdown sections and add appropriately. Lower priority but would clean up the workflow.

### 4. Fix or document PATH requirement

Either:
- Update skill doc to use absolute paths in all examples
- Add wrapper that sources user's shell profile
- Document that `todoist doctor` should be run at session start

## Test Cases to Add

1. `todoist add --project "@Work" --section "NonexistentSection"` → should fail gracefully
2. `todoist add --project "NonexistentProject"` → verify error message is helpful
3. Verify CLI works when invoked from different working directories

## Session Stats

- Tasks added: 14 total (across two batches)
- @Wait: 8 items
- @Ping: 4 items
- @Work: 2 items
- Failures: 2 (--section flag, retried without section)

## Related

- filing skill (produces the actions that feed into todoist)
- PATTERNS.md (should document Sublime Loop)
