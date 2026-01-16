---
name: todoist-gtd
user-invocable: false
description: >
  MCP-free Todoist integration with GTD coaching. Uses Python CLI (todoist) to query
  Todoist API v1 directly. Provides semantic understanding of the user's GTD structure (outcomes
  as sections, team vs personal, 3-tier ontology), query patterns, and outcome quality coaching.
  Also handles weekly review orchestration and pattern detection. Triggers on 'clean up outcomes',
  'team priorities', 'Q4 review', 'is this a good outcome', 'weekly review', 'am I overcommitting',
  'check my patterns', 'should I take this on', 'I said yes to', 'another meeting', 'they asked me to',
  'scope creep', 'this grew into', 'freedom score', or ANY Todoist-related task. (user)
---

# Todoist GTD

MCP-free Todoist integration using the official Python SDK (v1 API). Adds semantic understanding of the user's GTD structure and outcome quality coaching on top of the CLI's data access.

**Core insight:** The CLI provides data. This skill provides meaning.

## When to Use This Skill

**IMPORTANT: Invoke this skill BEFORE making Todoist queries.** The CLI doesn't know the user's GTD structure — this skill does. Without it, you'll query wrong fields (tasks vs sections), miss context (outcomes are sections, not tasks), and produce confusing results.

**Use for:**
- ANY Todoist query or update (load this skill first for context)
- "Help me clean up my Q1 outcomes"
- "Is the team working on the right things this quarter?"
- "Check my priorities against the yearly plan"
- "Is this a good outcome?"
- Weekly review / strategic reflection
- Creating or updating outcomes with proper structure
- Pattern detection: "Am I overcommitting?", "Check my patterns"
- Before taking on work: "Should I take this on?", "I said yes to..."

**NOT for:**
- Personal GTD Tier 3 tasks (not in scope for coaching, though queries are fine)

## Weekly Review Orchestration

Weekly review triggers a **three-phase workflow:**

1. **Filing** — Invoke **filing** skill first to clear cleanup zones
2. **Outcomes Review** — This skill: outcome health, staleness, Tier 2 vs 3 quality
3. **Pattern Reflection** — This skill: freedom score, pattern interrupts

**For detailed patterns:** See [references/PATTERNS.md](references/PATTERNS.md)

## Prerequisites

Before using this skill, verify the CLI is working:

```bash
# Pre-flight check
todoist doctor
```

**Expected:** All checks pass.

**If checks fail:**
- `command not found` → Run `scripts/install.sh`
- Dependency missing → Run `pip install -r requirements.txt`
- Not authenticated → Run `todoist auth`
- Wrapper missing → Run `scripts/install.sh`

**Dependencies** (should already be installed via `pip install -r requirements.txt`):
- `todoist-api-python>=3.0.0` — Official SDK
- `requests>=2.25.0` — OAuth token exchange
- `httpx>=0.24.0` — Timeout configuration

**System requirements:**
- Python 3.9+
- macOS Keychain (or `TODOIST_API_KEY` env var for Linux)
- Network access to api.todoist.com

## CLI Setup

The CLI source is `scripts/todoist.py` in this repo. A wrapper script at `~/.claude/scripts/todoist` provides the standard interface.

**Why the wrapper?**
- **Location independence** — works from any directory, not just the skill folder
- **Venv encapsulation** — handles Python environment so callers don't need to know about it
- **Single point of change** — if the script moves, only the wrapper needs updating

```bash
# Standard usage (all examples in this doc use this form)
todoist <command>

# If ~/.claude/scripts isn't in PATH, use absolute path:
~/.claude/scripts/todoist <command>
```

**Ensure `~/.claude/scripts` is in your PATH:**
```bash
# Add to ~/.zshrc or ~/.bashrc:
export PATH="$HOME/.claude/scripts:$PATH"
```

### Authentication

**Recommended: OAuth flow** (one-time setup)
```bash
todoist auth
# Browser opens → click "Authorize" → done
```

For SSH or remote sessions, use manual mode:
```bash
todoist auth --manual
# Copy URL → paste redirect URL back
```

Check authentication status:
```bash
todoist auth --status
```

**Fallback: Manual token** (if OAuth unavailable)
```bash
# 1. Get token from: https://todoist.com/prefs/integrations
# 2. Store in Keychain:
security add-generic-password -a "$USER" -s "todoist-api-key" -w "YOUR_TOKEN"
```

If auth fails, prompt user to run `todoist auth` or check their Keychain entry.

**Key design choice:** CLI shows ALL tasks by default. Unlike the MCP which defaults to hiding tasks assigned to others (`responsibleUserFiltering: "unassignedOrMe"`), this CLI shows everything. This prevents the duplicate-task bug where Claude couldn't see teammates' work.

### Error Handling

When CLI commands fail, use these patterns:

| Error | Likely Cause | Action |
|-------|--------------|--------|
| `not authenticated` | Token missing or cleared | Ask user to run `todoist auth` |
| `Token revoked or expired` | User revoked app access | Ask user to re-run `todoist auth` |
| `Request timed out` | Slow network or API issues | Retry once, then tell user |
| `Could not connect` | Network down | Tell user to check connection |
| `Rate limited` | Too many requests | Wait 30s and retry |
| `Task not found` | Bad task ID | Verify ID with user |
| `Cannot move between workspaces` | API limitation | Suggest complete + recreate |

**When to escalate to user:**
- Auth errors (they need to act)
- Repeated timeouts (might be their network)
- Permission errors (might need to unlock Keychain)

**When to retry silently:**
- Single timeout (transient)
- Single rate limit (just wait)

**When to suggest re-auth:**
- Any 401 error
- "Token revoked" message
- Repeated "not authenticated" after confirming auth status

## the user's Todoist Structure

**CRITICAL:** This structure differs from standard Todoist usage.

### Outcomes as Sections (not tasks!)

```
Desired Outcomes Q4 (project)
  ├── Made more of the LDC data usable... (section = outcome)
  │     └── [tasks under this section]
  ├── Laid the groundwork for 10x... (section = outcome)
  └── Built team capacity for 2026... (section = outcome)
```

**Why it matters:** Outcomes are SECTIONS, not tasks. Query with `sections`, not `tasks`.

### Key Projects

| Project | Purpose |
|---------|---------|
| `@Work` | Active work (Now/Later sections) |
| `Desired Outcomes Q4` / `H1` | Quarterly/half outcomes |
| `Areas of Focus` | AoF categories as sections |
| `@Claude` | Async inbox for Claude sessions (all contexts) |
| `Someday/Maybe` | Backlog |
| `@Wait` | Waiting for others |

**⚠️ GTD contexts (@Wait, @Claude, @Ping, @Time) are PROJECTS, not labels.** Query with `--project "@Wait"`, not `--label "waiting-for"`.

### Personal vs MIT Shared Projects

**This CLI connects to ONE account, but it contains BOTH personal and MIT shared projects.**

| Type | Projects | Visibility | Use For |
|------|----------|------------|---------|
| **Personal** | `Personal`, `@Home`, `Checklists/*` | Only user | Private outcomes, home tasks, personal reference |
| **MIT Shared** | `Desired Outcomes Q4`, `Desired Outcomes H1`, `Areas of Focus`, `@Work`, `HH:Lift`, `LDC:*`, `Clean Rooms`, `Technical Documentation` | Team can see | Work outcomes, team tasks, product boards |
| **GTD System** | `@Wait`, `@Ping`, `@Time`, `@Claude`, `Someday/Maybe` | Only user | GTD contexts (not outcomes) |

**⚠️ Critical distinction:**
- **`Personal` project** has a "Desired Outcomes" *section* → **private** personal outcomes
- **`Desired Outcomes Q4/H1`** are *projects* → **MIT shared** work outcomes

**When user says "add a personal outcome"** → `Personal` project, "Desired Outcomes" section
**When user says "add a work outcome"** → `Desired Outcomes Q4` or `H1` project

**The user also has a separate Team Todoist account** (not accessible via this CLI) for Tier 1 leadership priorities. When user mentions "team account", that's inaccessible here.

## Terminology Disambiguation

**"Project" has 3 meanings:**

| Context | Meaning | Example |
|---------|---------|---------|
| Todoist | Container for tasks | `Desired Outcomes Q4` project |
| GTD Tier 3 | Multi-step outcome | "Launch Panel+ v2" |
| Business | Work initiative | "The clean rooms project" |

**For full terminology guide:** See [references/TERMINOLOGY.md](references/TERMINOLOGY.md)

## The 3-Tier GTD Ontology

| Tier | What | Where in Todoist | Managed By |
|------|------|------------------|------------|
| **Tier 1** | Team Priorities | Team Todoist (not accessible here) | Leadership |
| **Tier 2** | Individual Outcomes | Sections in `Desired Outcomes Q4` | the user |
| **Tier 3** | Projects & Actions | Tasks under outcome sections | the user |

### Tier 2 vs Tier 3: The Critical Distinction

**Tier 2 asks:** "What do I want to have achieved?"
**Tier 3 asks:** "What do I need to do?"

**Quick test:**
- "Write the strategy doc" → Tier 3 (activity)
- "Team has clear Q4 direction" → Tier 2 (achievement)

**Rewrite examples (activity → achievement, verb-first past tense):**

| Activity language (bad) | Achievement language (good) |
|------------------------|----------------------------|
| Review Claude workspace MCP | Decided on workspace MCP authentication approach |
| Create Image generation skill | Created image generation skill for Claude to use NanoBanana |
| Build mega-beads synthesis tool | Figured out how to review and plan beads across Repos |
| Improve Conceptual Charts skill | Taught Claude how to make decent quality conceptual charts |

**The pattern:** Start with past-tense verb, describe what you'll *have done*, include the "so what" (why it matters or what decision it enables).

**For coaching patterns and examples:** See [references/COACHING.md](references/COACHING.md)

## CLI Query Patterns

**All commands return JSON.** Parse with jq or read directly.

### Get Account Overview
```bash
# List all projects
todoist projects

# Get sections in a project
todoist sections --project-id "<project-id>"
```

### Find Outcomes (Remember: sections, not tasks!)
```bash
# Get Q4 outcomes (sections in the outcomes project)
todoist sections --project-id "<desired-outcomes-q4-id>"

# Get tasks under a specific outcome
todoist tasks --section-id "<outcome-section-id>"
```

**No filtering gotcha:** CLI shows ALL tasks by default, including teammates' work.

### Check Claude Inbox
```bash
# Find @Claude project ID first
todoist projects | jq '.[] | select(.name == "@Claude")'

# Get tasks in @Claude inbox
todoist tasks --project-id "<claude-inbox-id>"
```

**Triage note:** Comments are included inline — check `.comments[]` for attachments and context before skipping items. See [references/PATTERNS.md](references/PATTERNS.md#inbox-triage-workflow) for the full workflow.

### Filter with Todoist Syntax
```bash
# Today's tasks (including overdue)
todoist filter "today"

# Assigned to someone
todoist filter "assigned to: Alex"

# By label
todoist filter "@waiting-for"

# Complex queries
todoist filter "#Work & today"
```

### Common Label Queries
```bash
todoist tasks --label "someday-maybe"
todoist tasks --label "areas-of-focus"
```

### Convenience Flags
```bash
# Filter by project name (not just ID)
todoist tasks --project "@Wait"

# Filter by assignee name (requires --project)
todoist tasks --project "Areas of Focus" --section-id "<id>" --assignee "Alex"

# Filter by creation date (for staleness checks)
todoist tasks --project "@Wait" --created-before "2025-12-01"

# Filter by age (convenience alternative to --created-before)
todoist tasks --project "@Wait" --older-than 30d   # 30 days
todoist tasks --project "@Wait" --older-than 2w    # 2 weeks
todoist tasks --project "@Wait" --older-than 3m    # 3 months

# Include section names in output (avoids manual section_id lookup)
todoist tasks --project "@Work" --include-section-name
```

## Data Model

**Task objects are complete.** The CLI returns tasks with comments inline:

```json
{
  "id": "...",
  "content": "Add this to the Team Handbook",
  "description": "",
  "comments": [
    { "content": "", "attachment": { "file_name": "document.pdf" } },
    { "content": "Progress note from UI", "attachment": null }
  ]
}
```

| Data | Location |
|------|----------|
| Task title | `content` field |
| Notes/details | `description` field |
| Due dates | `due` object |
| Attachments | `comments[].attachment` |
| Progress notes | `comments[].content` |

### Forwarded Emails Pattern

When emails are forwarded to a Todoist project's email address:
- Subject → task `content`
- Body → `comments[0]` with empty content, HTML attachment
- Attachments → additional `comments[]` entries with attachments

**Auth limitation:** Attachment URLs (`files.todoist.com`) require Todoist authentication. You cannot curl them directly — tell user to open in browser.

### Subtask Navigation

**Parent→child is one-way.** Tasks have `parent_id` pointing to their parent, but parents don't list their children.

```bash
# To find a task's parent:
# Read the parent_id field from the task JSON

# Note: CLI doesn't have --parent-id filter for listing subtasks
# Use filter syntax: todoist filter "subtask of: <parent-task-id>"
```

### Labels Limitation

**No label discovery endpoint.** You can filter by labels, but can't list all labels in an account. User must know label names.

```bash
todoist tasks --label "waiting-for"  # Works if label exists
# But no: list-all-labels                       # Doesn't exist
```

### Cross-Workspace Limitation

**Moving tasks between personal and shared projects fails.** The `move_task` API cannot move tasks across workspace boundaries (personal account ↔ MIT shared workspace).

**Workaround:** Complete the task in the source project, then recreate it in the target project. History is preserved in both locations.

```bash
# This fails:
todoist update <task-id> --project "Someday/Maybe"  # Error if crossing workspace

# Workaround:
todoist add "Task content" --project "Someday/Maybe"
todoist done <old-task-id>
```

## Write Operation Guardrails

### Creating Outcomes

**BEFORE creating, always ask:**
1. Is this Tier 2 (achievement) or Tier 3 (activity)?
2. Which Team Priority does it serve?
3. What does success look like?

**Outcome goes in:** A section in `Desired Outcomes Q4/H1`
**Tasks go under:** That outcome section

```bash
# DON'T create outcome as a task
todoist add "Build team documentation"  # WRONG

# DO discuss and create as section
todoist add-section "Built team capacity through documentation" \
  --project-id "<desired-outcomes-q4>"  # CORRECT
```

### Completing vs Deleting Tasks

**ALWAYS complete, NEVER delete.**

```bash
todoist done "<task-id>"  # CORRECT - preserves history
# No delete command in CLI         # By design - prevents history loss
```

Why this matters:
- Completed tasks show in stats and activity logs
- Completion history informs future planning ("what did we achieve last quarter?")
- Duplicates should be completed with a note, not deleted

**Use cases:**
- Task done → `todoist done <id>`
- Task is duplicate → complete it (history shows it was captured)
- Task obsolete → complete it (still counts as "resolved")
- Task moved elsewhere → complete it with a note in Todoist

**Before completing outcomes (sections):** Prompt for reflection:
- "What did we learn?"
- "What comes next?"

### Writing Next Actions (GTD Style)

**Next actions must be concrete, physical, and start with a verb describing what you'd actually do.**

Bad (vague, outcome-ish):
- "Sort out the legal stuff"
- "2026 planning"
- "Marketing Week articles"

Good (concrete, physical):
- "Read EK doc and note 3 questions for Ella meeting"
- "Open CS&P 2026 deck + H1 outcomes list, draft team plan skeleton"
- "Open Marketing Week folder, pick one article idea, write first draft"

**The test:** "What would I actually do when I sit down to do this?"

If the answer isn't immediately obvious from the task title, it's not a next action - it's a project or outcome that needs breaking down.

### Anti-Patterns

| Bad Practice | Why Wrong | Better |
|--------------|-----------|--------|
| Creating outcome as task | Confuses structure | Use `add-section` |
| Tier 3 project as outcome | Inflates outcome count | Challenge: "Is this activity or achievement?" |
| Outcome without Team Priority | Orphan work | Ask: "Which priority does this serve?" |
| Completing without reflection | Loses learning | Prompt for resolution notes |

## Pattern Intervention Triggers

Surface these concerns when analyzing data:

**Overcommitment signals:**
- 5+ active outcomes → "Can you really advance all of these?"
- All outcomes P1 → "If everything is critical, nothing is focused"

**Strategic gaps:**
- Outcome has no tasks → "This outcome has no active work - stuck or deprioritized?"
- No outcomes in an AoF → "This area is dormant - intentional?"

**Staleness signals:**
- Outcome unchanged 4+ weeks → "Stuck, deprioritized, or needs rescoping?"
- Growing Someday/Maybe → "Commitment backlog or idea capture?"

**Quality signals:**
- Outcome reads like activity → "This is what you're doing, not what you're achieving"
- Missing success criteria → "How will you know when it's done?"

## Claude Inbox Patterns

### Session Start Behavior

1. **Query the @Claude inbox:**
   ```bash
   todoist tasks --project "@Claude"
   ```
   Returns complete tasks with `.comments[]` inline — no separate calls needed.

2. **Surface items:** "You have X items in @Claude..."

3. **For each item:** Check `.comments[]` for attachments/context, then decide: bead, skip, move, or do now.

See [references/PATTERNS.md](references/PATTERNS.md#inbox-triage-workflow) for the full triage workflow.

## Common Analysis Workflows

### "Clean up my Q1 outcomes"

1. Get outcomes: `todoist sections --project-id "<desired-outcomes-q1>"`
2. For each outcome, check:
   - Is it achievement language? (Tier 2 test)
   - Does it have active work? `todoist tasks --section-id "<id>"`
   - Is it still relevant?
3. Surface: "You have X outcomes. 3 have no active tasks. 2 read like activities."

### "Is the team working on the right things?"

1. Get team-relevant outcomes
2. Cross-reference with Team Priorities (from memory/discussion)
3. Surface: "Outcomes X and Y align with Priority A. Outcome Z seems orphaned."

### "Prepare for 1-1 with Alex"

```bash
todoist filter "assigned to: Alex"
todoist filter "assigned to: Alex & @waiting-for"
```

Surface: "Alex has X outcomes, Y waiting-fors. [Summary of each]"

## Integration with Other Skills

**Coordinates with:**
- **filing** - Weekly review starts with filing cleanup
- **google-workspace** - For document research related to outcomes

**Pattern:** This skill combines data (CLI queries) with judgment (pattern detection, coaching).

## Quick Reference

### Key Queries

| Query | CLI Command |
|-------|-------------|
| All projects | `todoist projects` |
| All outcomes | `todoist sections --project "Desired Outcomes Q1"` |
| Tasks under outcome | `todoist tasks --section-id "<outcome-id>"` |
| Tasks with section names | `todoist tasks --project "@Work" --include-section-name` |
| Person's work | `todoist tasks --project "X" --assignee "Name"` |
| Waiting-fors | `todoist tasks --project "@Wait"` |
| Stale waiting-fors | `todoist tasks --project "@Wait" --older-than 30d` |
| Someday/Maybe | `todoist tasks --label "someday-maybe"` |
| @Claude inbox | `todoist tasks --project "@Claude"` |
| Today's tasks | `todoist filter "today"` |

**Note:** `tasks` and `task` return complete objects with `.comments[]` inline. `filter` returns tasks only (no comments — intentional, as filters can span projects and N+1 API calls would be slow).

### Key Write Operations

| Operation | CLI Command |
|-----------|-------------|
| Create outcome | `todoist add-section "name" --project "Desired Outcomes Q1"` |
| Create task | `todoist add "content" --project "@Work" --section "Now"` |
| Complete task | `todoist done "<task-id>"` |
| Rename task | `todoist update "<task-id>" --content "new name"` |
| Move to project | `todoist update "<task-id>" --project "@Ping"` |
| Move to section | `todoist update "<task-id>" --section "Now"` |
| Move to project+section | `todoist update "<task-id>" --project "@Work" --section "Now"` |

## Success Metrics

**Good analysis achieves:**
- User understands outcome health (active, stale, orphaned)
- Tier confusion corrected (activity → achievement)
- Strategic alignment visible (outcomes → priorities)
- Pattern concerns raised proactively

**Signs of poor analysis:**
- Just listing data without patterns
- Missing the "so what?" - data without insight
- Not challenging potential issues

## Remember

**The CLI is plumbing. This skill is meaning.**

- Outcomes are SECTIONS, not tasks
- "Project" means different things in different contexts
- Challenge activity language → frame as achievement
- Surface patterns, not just data
- Raise pattern concerns proactively
- CLI shows ALL tasks by default — no hidden filtering gotcha
