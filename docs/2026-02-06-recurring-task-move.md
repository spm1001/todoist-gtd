# Field Report: Recurring task loses recurrence when moved to @Claude

**Date:** 2026-02-06
**Context:** @Claude inbox triage during /close session
**Severity:** Low (data loss is minimal, but confusing)

## What Happened

User has a recurring task "Check Home Assistant" in its original project. At some point it was moved to the @Claude project (to flag it for a Claude session — meaning "get Claude to check out my HA box"). The task appeared in @Claude as a plain task with no recurrence metadata.

During triage, it looked like a 124-day-old stale item (created 2025-10-05). In reality, it was a recent move of a recurring task — the age reflects the original creation date, not when it landed in @Claude.

## The Gap

The triage workflow in the todoist-gtd skill has no way to distinguish:
1. A task that was *created* in @Claude 124 days ago (genuinely stale)
2. A recurring task that was *moved* to @Claude recently (fresh intent, old creation date)

The CLI returns `created_at` but not `moved_at` or any recurrence history. The Todoist API may not expose this either.

## Suggested Improvements

1. **Staleness heuristic:** When flagging old tasks, also check `updated_at`. If `updated_at` is recent but `created_at` is old, note: "This task was recently modified — it may have been moved here rather than created here."

2. **Triage prompt:** When surfacing items, add a note for tasks where `updated_at` - `created_at` > 30 days: "Age may be misleading — task was updated recently."

3. **Vague imperative detection:** Tasks like "Check X" with no description or comments could be flagged as potentially-recurring during triage, prompting the user to clarify intent.

## Resolution

User clarified the intent (wants Claude to check HA box) and will pick it up in a separate session. The task was left in @Claude.
