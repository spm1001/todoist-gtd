---
name: todoist-gtd
user-invocable: false
description: >
  MCP-free Todoist integration with GTD coaching. Uses Python CLI (scripts/todoist.py) to query
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

## CLI Setup

The CLI lives at `scripts/todoist.py` in this skill folder. A wrapper script provides a shorter path:

```bash
# Short form (wrapper in ~/.claude/scripts/)
todoist <command>

# Long form (if wrapper not in PATH)
~/.claude/.venv/bin/python scripts/todoist.py <command>
```

**Ensure `~/.claude/scripts` is in your PATH** for the short form to work:
```bash
# Add to ~/.zshrc or ~/.bashrc:
export PATH="$HOME/.claude/scripts:$PATH"
```

### Authentication

**Recommended: OAuth flow** (one-time setup)
```bash
~/.claude/.venv/bin/python scripts/todoist.py auth
# Browser opens → click "Authorize" → done
```

For SSH or remote sessions, use manual mode:
```bash
~/.claude/.venv/bin/python scripts/todoist.py auth --manual
# Copy URL → paste redirect URL back
```

Check authentication status:
```bash
~/.claude/.venv/bin/python scripts/todoist.py auth --status
```

**Fallback: Manual token** (if OAuth unavailable)
```bash
# 1. Get token from: https://todoist.com/prefs/integrations
# 2. Store in Keychain:
security add-generic-password -a "$USER" -s "todoist-api-key" -w "YOUR_TOKEN"
```

If auth fails, prompt user to run `todoist.py auth` or check their Keychain entry.

**Key design choice:** CLI shows ALL tasks by default. Unlike the MCP which defaults to hiding tasks assigned to others (`responsibleUserFiltering: "unassignedOrMe"`), this CLI shows everything. This prevents the duplicate-task bug where Claude couldn't see teammates' work.

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
scripts/todoist.py projects

# Get sections in a project
scripts/todoist.py sections --project-id "<project-id>"
```

### Find Outcomes (Remember: sections, not tasks!)
```bash
# Get Q4 outcomes (sections in the outcomes project)
scripts/todoist.py sections --project-id "<desired-outcomes-q4-id>"

# Get tasks under a specific outcome
scripts/todoist.py tasks --section-id "<outcome-section-id>"
```

**No filtering gotcha:** CLI shows ALL tasks by default, including teammates' work.

### Check Claude Inbox
```bash
# Find @Claude project ID first
scripts/todoist.py projects | jq '.[] | select(.name == "@Claude")'

# Get tasks in @Claude inbox
scripts/todoist.py tasks --project-id "<claude-inbox-id>"
```

**Triage note:** Comments are included inline — check `.comments[]` for attachments and context before skipping items. See [references/PATTERNS.md](references/PATTERNS.md#inbox-triage-workflow) for the full workflow.

### Filter with Todoist Syntax
```bash
# Today's tasks (including overdue)
scripts/todoist.py filter "today"

# Assigned to someone
scripts/todoist.py filter "assigned to: Alex"

# By label
scripts/todoist.py filter "@waiting-for"

# Complex queries
scripts/todoist.py filter "#Work & today"
```

### Common Label Queries
```bash
scripts/todoist.py tasks --label "someday-maybe"
scripts/todoist.py tasks --label "areas-of-focus"
```

### Convenience Flags
```bash
# Filter by project name (not just ID)
scripts/todoist.py tasks --project "@Wait"

# Filter by assignee name (requires --project)
scripts/todoist.py tasks --project "Areas of Focus" --section-id "<id>" --assignee "Alex"

# Filter by creation date (for staleness checks)
scripts/todoist.py tasks --project "@Wait" --created-before "2025-12-01"

# Filter by age (convenience alternative to --created-before)
scripts/todoist.py tasks --project "@Wait" --older-than 30d   # 30 days
scripts/todoist.py tasks --project "@Wait" --older-than 2w    # 2 weeks
scripts/todoist.py tasks --project "@Wait" --older-than 3m    # 3 months

# Include section names in output (avoids manual section_id lookup)
scripts/todoist.py tasks --project "@Work" --include-section-name
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
# Use filter syntax: scripts/todoist.py filter "subtask of: <parent-task-id>"
```

### Labels Limitation

**No label discovery endpoint.** You can filter by labels, but can't list all labels in an account. User must know label names.

```bash
scripts/todoist.py tasks --label "waiting-for"  # Works if label exists
# But no: list-all-labels                       # Doesn't exist
```

### Cross-Workspace Limitation

**Moving tasks between personal and shared projects fails.** The `move_task` API cannot move tasks across workspace boundaries (personal account ↔ MIT shared workspace).

**Workaround:** Complete the task in the source project, then recreate it in the target project. History is preserved in both locations.

```bash
# This fails:
scripts/todoist.py update <task-id> --project "Someday/Maybe"  # Error if crossing workspace

# Workaround:
scripts/todoist.py add "Task content" --project "Someday/Maybe"
scripts/todoist.py done <old-task-id>
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
scripts/todoist.py add "Build team documentation"  # WRONG

# DO discuss and create as section
scripts/todoist.py add-section "Built team capacity through documentation" \
  --project-id "<desired-outcomes-q4>"  # CORRECT
```

### Completing vs Deleting Tasks

**ALWAYS complete, NEVER delete.**

```bash
scripts/todoist.py done "<task-id>"  # CORRECT - preserves history
# No delete command in CLI         # By design - prevents history loss
```

Why this matters:
- Completed tasks show in stats and activity logs
- Completion history informs future planning ("what did we achieve last quarter?")
- Duplicates should be completed with a note, not deleted

**Use cases:**
- Task done → `scripts/todoist.py done <id>`
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
   scripts/todoist.py tasks --project "@Claude"
   ```
   Returns complete tasks with `.comments[]` inline — no separate calls needed.

2. **Surface items:** "You have X items in @Claude..."

3. **For each item:** Check `.comments[]` for attachments/context, then decide: bead, skip, move, or do now.

See [references/PATTERNS.md](references/PATTERNS.md#inbox-triage-workflow) for the full triage workflow.

## Common Analysis Workflows

### "Clean up my Q1 outcomes"

1. Get outcomes: `scripts/todoist.py sections --project-id "<desired-outcomes-q1>"`
2. For each outcome, check:
   - Is it achievement language? (Tier 2 test)
   - Does it have active work? `scripts/todoist.py tasks --section-id "<id>"`
   - Is it still relevant?
3. Surface: "You have X outcomes. 3 have no active tasks. 2 read like activities."

### "Is the team working on the right things?"

1. Get team-relevant outcomes
2. Cross-reference with Team Priorities (from memory/discussion)
3. Surface: "Outcomes X and Y align with Priority A. Outcome Z seems orphaned."

### "Prepare for 1-1 with Alex"

```bash
scripts/todoist.py filter "assigned to: Alex"
scripts/todoist.py filter "assigned to: Alex & @waiting-for"
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
| All projects | `scripts/todoist.py projects` |
| All outcomes | `scripts/todoist.py sections --project "Desired Outcomes Q1"` |
| Tasks under outcome | `scripts/todoist.py tasks --section-id "<outcome-id>"` |
| Tasks with section names | `scripts/todoist.py tasks --project "@Work" --include-section-name` |
| Person's work | `scripts/todoist.py tasks --project "X" --assignee "Name"` |
| Waiting-fors | `scripts/todoist.py tasks --project "@Wait"` |
| Stale waiting-fors | `scripts/todoist.py tasks --project "@Wait" --older-than 30d` |
| Someday/Maybe | `scripts/todoist.py tasks --label "someday-maybe"` |
| @Claude inbox | `scripts/todoist.py tasks --project "@Claude"` |
| Today's tasks | `scripts/todoist.py filter "today"` |

**Note:** `tasks` and `task` return complete objects with `.comments[]` inline. `filter` returns tasks only (no comments — intentional, as filters can span projects and N+1 API calls would be slow).

### Key Write Operations

| Operation | CLI Command |
|-----------|-------------|
| Create outcome | `scripts/todoist.py add-section "name" --project "Desired Outcomes Q1"` |
| Create task | `scripts/todoist.py add "content" --project "@Work" --section "Now"` |
| Complete task | `scripts/todoist.py done "<task-id>"` |
| Rename task | `scripts/todoist.py update "<task-id>" --content "new name"` |
| Move to project | `scripts/todoist.py update "<task-id>" --project "@Ping"` |
| Move to section | `scripts/todoist.py update "<task-id>" --section "Now"` |
| Move to project+section | `scripts/todoist.py update "<task-id>" --project "@Work" --section "Now"` |

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
