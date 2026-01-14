# Pattern Interrupts & Weekly Review

Behavioral patterns to detect and strategic reflection for weekly review.

## The Four Traps

Patterns that undermine stated intentions. When detected, surface with questions — not judgment.

| Pattern | Signal | Intervention Question |
|---------|--------|----------------------|
| **Overcommitment** | Adding to plate without questioning | "Should this be delegated, declined, or is it genuinely yours?" |
| **Execution Without Reflection** | Clarifying/organizing before reflecting on whether it matters | "Does this still matter?" |
| **Hero Mode** | Solving for others instead of building their capability | "What question could you ask instead that builds their capability?" |
| **Scope Creep** | X becomes X+Y+Z without conscious choice | "This started as X, now it's X+Y+Z. Intentional or drift?" |

**Philosophy:** Support intentions, not enforce rules. The goal is conscious choice, not compliance.

## Freedom to Be Curious

**Target:** 7/10

Primary metric for whether the GTD system is working. Low score = overcommitted, reactive, no space for exploration.

**Measured by:**
- Time in exploratory thinking vs reactive execution
- Number of "shoulds" declined this week
- Presence of unscheduled thinking time in calendar
- Quality of sleep (proxy for mental load)

**Weekly review prompt:** "What's your curiosity freedom score this week? What's one thing you could decline?"

## Weekly Review Orchestration

"Weekly review" triggers a **three-phase workflow:**

### Phase 1: Filing
Invoke **filing** skill first:
- Tidy cleanup zones (Downloads, iCloud, Desktop, iA Writer, Drive inbox)
- Clear the physical/digital clutter before strategic reflection

### Phase 2: Outcomes Review
This skill (todoist-gtd):
- Check outcome health (stale, orphaned, activity-language)
- Review against Team Priorities
- Target: 3-5 active Tier 2 outcomes
- Surface: "You have N outcomes. The target is 3-5. Which ones are actually Tier 3 projects?"

### Phase 3: Pattern Reflection
Still this skill, using patterns above:
- Check freedom score
- Surface any detected patterns (overcommitment, scope creep, etc.)
- Ask: "What's one thing you could decline this week?"

## Inbox Triage Workflow

When processing @Claude or any inbox project:

### The Process

```
1. Get all items (comments included inline)
   scripts/todoist.py tasks --project "@Claude"

2. For EACH item, check .comments[] then decide:
   - bead: Create issue, complete task
   - skip: Complete task (context-lost or not actionable)
   - move: Update task to different project/section
   - do now: Handle immediately, complete task

3. Execute:
   - done <id>                           # Complete
   - update <id> --project "@Ping"       # Move to project
   - update <id> --section "Now"         # Move to section
   - update <id> --content "better name" # Rename

4. Report summary
   "Processed X items: Y beaded, Z moved, W skipped"
```

### Reading Comments

Comments are inline on each task as `.comments[]`. Look for:

| Pattern | Meaning |
|---------|---------|
| `comments: []` | No hidden context — what you see is what you get |
| `comments[].content` has text | UI-added progress notes |
| `comments[].attachment` exists | File attached (PDF, image, etc.) |
| `comments[].content` empty + attachment is HTML | Forwarded email body |

### Common Triage Decisions

| Signal | Likely Disposition |
|--------|-------------------|
| Has attachments in `.comments[]` | Worth investigating — bead or do |
| Empty comments array | Probably quick capture — skip or do |
| Clear next action | Do now or move to @Work |
| Complex/multi-step | Bead it |

## When to Invoke Patterns

**Proactive triggers:**
- Weekly review (always)
- "Am I overcommitting?"
- "Check my patterns"
- "Should I take this on?"
- "I said yes to..."
- "Another meeting..."
- "They asked me to..."
- "This grew into..."

**Reactive triggers (when you notice):**
- User adding work without questioning if it's theirs
- Scope expanding mid-conversation
- Solving problems that could build others' capability
- Execution without reflecting on whether it matters

## Integration with Todoist Data

Pattern detection is more powerful when combined with data:

| Pattern | Todoist Signal |
|---------|---------------|
| Overcommitment | 5+ active outcomes, all P1 |
| Scope Creep | Outcome task count growing significantly |
| Execution Without Reflection | Tasks completed but outcomes unchanged |
| Hero Mode | Many tasks assigned to user that could be delegated |

Surface data patterns alongside intervention questions.
