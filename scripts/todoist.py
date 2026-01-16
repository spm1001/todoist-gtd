#!/usr/bin/env python3
"""
Todoist CLI - MCP-free interface using official Python SDK.

Usage:
    todoist.py <command> [options]

Commands:
    auth                Authenticate with Todoist (OAuth flow)
    auth --status       Check authentication status
    auth --manual       Use manual mode (for SSH)
    projects            List all projects
    sections            List sections (--project or --project-id to filter)
    tasks               List tasks with comments inline
                        Supports --project, --section, --older-than, --include-section-name
    task ID             Get single task with comments inline
    filter QUERY        Filter tasks (no comments - can return many)
    done ID             Complete a task
    add CONTENT         Create a new task (--project, --section for placement)
    update ID           Update/move task (--content, --project, --section, etc.)
    add-section NAME    Create a new section (--project or --project-id)
    comments            Get comments standalone (rarely needed)
    collaborators       Get project collaborators (requires --project-id)

Authentication:
    Run `todoist.py auth` to authenticate via OAuth (recommended).
    Or set TODOIST_API_KEY environment variable.
    On macOS, can also use Keychain:
        security add-generic-password -a "$USER" -s "todoist-api-key" -w "TOKEN"
"""

import argparse
import json
import re
import subprocess
import sys
from typing import Any

from todoist_secrets import get_token

# Lazy import to allow --help without SDK installed
TodoistAPI = None


DEFAULT_TIMEOUT = 30  # seconds


def get_api():
    """Get authenticated TodoistAPI instance with timeout."""
    global TodoistAPI
    if TodoistAPI is None:
        try:
            from todoist_api_python.api import TodoistAPI as API
            TodoistAPI = API
        except ImportError:
            print("Error: todoist-api-python not installed", file=sys.stderr)
            print("\nInstall with: pip install todoist-api-python", file=sys.stderr)
            sys.exit(1)

    token = get_token()
    # Configure httpx session with timeout
    import httpx
    session = httpx.Client(timeout=DEFAULT_TIMEOUT)
    return TodoistAPI(token, session=session)


def to_dict(obj: Any) -> dict:
    """Convert SDK object to dict for JSON output."""
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()
    if hasattr(obj, '__dict__'):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
    return obj


def collect_paginated(iterator) -> list:
    """Collect all items from a paginated SDK iterator."""
    items = []
    for batch in iterator:
        items.extend(batch)
    return items


def output_json(data: Any):
    """Output data as JSON."""
    if isinstance(data, list):
        print(json.dumps([to_dict(item) for item in data], indent=2, default=str))
    else:
        print(json.dumps(to_dict(data), indent=2, default=str))


def handle_task_not_found(e: Exception, task_id: str):
    """Handle task not found errors with clean message."""
    error_str = str(e).lower()
    # Todoist returns 400 for invalid IDs, 404 for valid-format but missing
    if "404" in error_str or "not found" in error_str or "400" in error_str:
        print(f"Error: Task '{task_id}' not found or invalid", file=sys.stderr)
        sys.exit(1)
    # Re-raise if it's a different error
    raise


def resolve_project(api, name_or_id: str) -> str:
    """Resolve a project name to ID. If already an ID, return as-is."""
    # Always try name lookup first - handles names like "Personal", "Inbox"
    projects = collect_paginated(api.get_projects())
    name_lower = name_or_id.lower()
    for p in projects:
        if p.name.lower() == name_lower:
            return p.id

    # Not found by name - if it looks like it could be an ID, return as-is
    if name_or_id and ' ' not in name_or_id:
        return name_or_id

    print(f"Error: Project '{name_or_id}' not found", file=sys.stderr)
    sys.exit(1)


def resolve_section(api, project_id: str, name_or_id: str) -> str:
    """Resolve a section name to ID within a project. If already an ID, return as-is."""
    # If it looks like an ID (alphanumeric, no spaces), assume it's an ID
    if name_or_id and ' ' not in name_or_id and len(name_or_id) < 20:
        # Could be an ID - but also could be a short name like "Now"
        # Try to find by name first, fall back to treating as ID
        sections = collect_paginated(api.get_sections(project_id=project_id))
        name_lower = name_or_id.lower()
        for s in sections:
            if s.name.lower() == name_lower:
                return s.id
        # Not found by name - assume it's an ID
        return name_or_id

    # Search by name
    sections = collect_paginated(api.get_sections(project_id=project_id))
    name_lower = name_or_id.lower()
    for s in sections:
        if s.name.lower() == name_lower:
            return s.id

    print(f"Error: Section '{name_or_id}' not found in project", file=sys.stderr)
    sys.exit(1)


def resolve_assignee(api, project_id: str, name_or_email: str) -> str:
    """Resolve an assignee name/email to user ID."""
    collaborators = collect_paginated(api.get_collaborators(project_id))
    name_lower = name_or_email.lower()

    for c in collaborators:
        if c.name.lower() == name_lower or c.email.lower() == name_lower:
            return c.id

    print(f"Error: Collaborator '{name_or_email}' not found in project", file=sys.stderr)
    sys.exit(1)


def cmd_get_projects(args):
    """List all projects."""
    api = get_api()
    projects = collect_paginated(api.get_projects())
    output_json(projects)


def cmd_get_sections(args):
    """List sections."""
    api = get_api()

    # Resolve project name to ID if provided
    project_id = args.project_id
    if args.project:
        project_id = resolve_project(api, args.project)

    sections = collect_paginated(api.get_sections(project_id=project_id))
    output_json(sections)


def cmd_get_tasks(args):
    """List tasks with optional filters."""
    api = get_api()

    # Resolve project name to ID if provided
    project_id = args.project_id
    if args.project:
        project_id = resolve_project(api, args.project)

    # Resolve section name to ID if provided
    section_id = args.section_id
    if args.section:
        if not project_id:
            print("Error: --section requires --project or --project-id", file=sys.stderr)
            sys.exit(1)
        section_id = resolve_section(api, project_id, args.section)

    tasks = collect_paginated(api.get_tasks(
        project_id=project_id,
        section_id=section_id,
        label=args.label
    ))

    # Filter by assignee if provided (client-side filter)
    if args.assignee:
        if not project_id:
            print("Error: --assignee requires --project or --project-id to resolve collaborator", file=sys.stderr)
            sys.exit(1)
        assignee_id = resolve_assignee(api, project_id, args.assignee)
        tasks = [t for t in tasks if getattr(t, 'assignee_id', None) == assignee_id]

    # Filter by creation date if provided (client-side filter)
    if args.created_before and args.older_than:
        print("Error: Cannot use both --older-than and --created-before", file=sys.stderr)
        sys.exit(1)

    if args.created_before or args.older_than:
        from datetime import datetime, timedelta

        def get_created(t):
            ca = t.created_at
            if isinstance(ca, str):
                return datetime.fromisoformat(ca[:19])
            return ca.replace(tzinfo=None)  # datetime object

        if args.older_than:
            match = re.match(r'(\d+)([dwm])', args.older_than)
            if not match:
                print("Error: --older-than format should be like '30d', '2w', or '3m'", file=sys.stderr)
                sys.exit(1)
            num, unit = int(match.group(1)), match.group(2)
            days = num * {'d': 1, 'w': 7, 'm': 30}[unit]
            cutoff = datetime.now() - timedelta(days=days)
        else:
            cutoff = datetime.fromisoformat(args.created_before + "T23:59:59")

        tasks = [t for t in tasks if get_created(t) < cutoff]

    # Enrich tasks with comments (only fetch if task has any — avoids unnecessary API calls)
    enriched = []
    for t in tasks:
        task_dict = to_dict(t)
        if getattr(t, 'comment_count', 0) > 0:
            comments = collect_paginated(api.get_comments(task_id=t.id))
            task_dict['comments'] = [to_dict(c) for c in comments]
        else:
            task_dict['comments'] = []
        enriched.append(task_dict)

    # Optionally include section names (requires extra API call)
    if args.include_section_name:
        if not project_id:
            print("Warning: --include-section-name requires --project to work, ignoring", file=sys.stderr)
        else:
            sections = {s.id: s.name for s in collect_paginated(api.get_sections(project_id=project_id))}
            for task_dict in enriched:
                sid = task_dict.get('section_id')
                task_dict['section_name'] = sections.get(sid) if sid else None

    print(json.dumps(enriched, indent=2, default=str))


def cmd_get_task(args):
    """Get a single task with comments."""
    api = get_api()
    try:
        task = api.get_task(args.id)
    except Exception as e:
        handle_task_not_found(e, args.id)
    task_dict = to_dict(task)
    if getattr(task, 'comment_count', 0) > 0:
        comments = collect_paginated(api.get_comments(task_id=args.id))
        task_dict['comments'] = [to_dict(c) for c in comments]
    else:
        task_dict['comments'] = []
    print(json.dumps(task_dict, indent=2, default=str))


def cmd_filter_tasks(args):
    """Filter tasks using Todoist filter syntax."""
    api = get_api()
    tasks = collect_paginated(api.filter_tasks(query=args.query))
    output_json(tasks)


def cmd_complete_task(args):
    """Complete a task."""
    api = get_api()
    try:
        success = api.complete_task(args.id)
    except Exception as e:
        handle_task_not_found(e, args.id)
    print(json.dumps({"success": success, "task_id": args.id}))


def cmd_add_task(args):
    """Create a new task."""
    api = get_api()

    # Resolve project name to ID if provided
    project_id = args.project_id
    if args.project:
        project_id = resolve_project(api, args.project)

    # Resolve section name to ID if provided
    section_id = args.section_id
    if args.section:
        if not project_id:
            print("Error: --section requires --project or --project-id", file=sys.stderr)
            sys.exit(1)
        section_id = resolve_section(api, project_id, args.section)

    labels = args.labels.split(",") if args.labels else None

    task = api.add_task(
        content=args.content,
        description=args.description,
        project_id=project_id,
        section_id=section_id,
        parent_id=args.parent_id,
        labels=labels,
        priority=args.priority,
        due_string=args.due
    )
    output_json(task)


def cmd_update_task(args):
    """Update an existing task."""
    api = get_api()

    # Resolve project name to ID if provided
    project_id = args.project_id
    if args.project:
        project_id = resolve_project(api, args.project)

    # Resolve section name to ID if provided
    section_id = args.section_id
    if args.section:
        # Need a project context to resolve section name
        if project_id:
            # Moving to new project - resolve section in target project
            resolve_project_id = project_id
        else:
            # Not moving - resolve section in task's current project
            try:
                task = api.get_task(args.id)
            except Exception as e:
                handle_task_not_found(e, args.id)
            resolve_project_id = task.project_id
        section_id = resolve_section(api, resolve_project_id, args.section)

    # Separate update fields from move fields
    # update_task() handles: content, description, labels, priority, due
    # move_task() handles: project_id, section_id, parent_id
    update_kwargs = {}
    if args.content:
        update_kwargs['content'] = args.content
    if args.description is not None:
        update_kwargs['description'] = args.description
    if args.priority:
        update_kwargs['priority'] = args.priority
    if args.due:
        update_kwargs['due_string'] = args.due
    if args.labels:
        update_kwargs['labels'] = args.labels.split(",")

    move_kwargs = {}
    if project_id:
        move_kwargs['project_id'] = project_id
    if section_id:
        move_kwargs['section_id'] = section_id

    if not update_kwargs and not move_kwargs:
        print("Error: No update parameters provided", file=sys.stderr)
        sys.exit(1)

    # Perform move first (if needed), then update
    if move_kwargs:
        try:
            api.move_task(args.id, **move_kwargs)
        except Exception as e:
            error_str = str(e).lower()
            if "404" in error_str or "not found" in error_str:
                print(f"Error: Task '{args.id}' not found", file=sys.stderr)
                sys.exit(1)
            if "429" in str(e) or "rate limit" in error_str:
                print("Error: Rate limited by Todoist. Wait a moment and retry.", file=sys.stderr)
                sys.exit(1)
            if "400" in str(e):
                # Try to give specific error messages for common 400 causes
                if "workspace" in error_str or "project_id" in error_str:
                    print("Error: Cannot move task between workspaces (personal ↔ team).", file=sys.stderr)
                    print("Workaround: Complete the task and recreate it in the target project.", file=sys.stderr)
                else:
                    # Unknown 400 error - show the actual message
                    print(f"Error: Move failed - {e}", file=sys.stderr)
                sys.exit(1)
            raise

    if update_kwargs:
        try:
            api.update_task(args.id, **update_kwargs)
        except Exception as e:
            handle_task_not_found(e, args.id)

    # Fetch and show the updated task
    try:
        task = api.get_task(args.id)
    except Exception as e:
        handle_task_not_found(e, args.id)
    output_json(task)


def cmd_add_section(args):
    """Create a new section."""
    api = get_api()

    # Resolve project name to ID if provided
    project_id = args.project_id
    if args.project:
        project_id = resolve_project(api, args.project)

    if not project_id:
        print("Error: --project-id or --project is required for add-section", file=sys.stderr)
        sys.exit(1)

    section = api.add_section(
        name=args.name,
        project_id=project_id
    )
    output_json(section)


def cmd_get_comments(args):
    """Get comments for a task or project."""
    api = get_api()

    if not args.task_id and not args.project_id:
        print("Error: --task-id or --project-id is required", file=sys.stderr)
        sys.exit(1)

    comments = collect_paginated(api.get_comments(
        task_id=args.task_id,
        project_id=args.project_id
    ))
    output_json(comments)


def cmd_get_collaborators(args):
    """Get collaborators for a project."""
    api = get_api()

    if not args.project_id:
        print("Error: --project-id is required", file=sys.stderr)
        sys.exit(1)

    collaborators = collect_paginated(api.get_collaborators(args.project_id))
    output_json(collaborators)


def cmd_auth(args):
    """Authenticate with Todoist."""
    from todoist_auth import authenticate, get_auth_status

    if args.status:
        status = get_auth_status()
        print(status["message"])
        sys.exit(0 if status["authenticated"] else 1)

    success = authenticate(manual=args.manual, code=args.code)
    sys.exit(0 if success else 1)


def cmd_doctor(args):
    """Check CLI setup and diagnose issues."""
    import os
    import shutil
    from pathlib import Path

    checks_passed = 0
    checks_failed = 0

    def check(name: str, passed: bool, detail: str = ""):
        nonlocal checks_passed, checks_failed
        if passed:
            checks_passed += 1
            print(f"  ✓ {name}")
        else:
            checks_failed += 1
            print(f"  ✗ {name}")
            if detail:
                print(f"    → {detail}")

    print("Checking todoist-gtd setup...\n")

    # Python version
    print("[Python]")
    py_version = sys.version_info
    check(
        f"Python {py_version.major}.{py_version.minor}.{py_version.micro}",
        py_version >= (3, 9),
        "Requires Python 3.9+" if py_version < (3, 9) else ""
    )

    # Dependencies
    print("\n[Dependencies]")
    for pkg in ["todoist_api_python", "requests", "httpx"]:
        try:
            __import__(pkg)
            check(pkg, True)
        except ImportError:
            check(pkg, False, f"pip install {pkg.replace('_', '-')}")

    # Wrapper script
    print("\n[Wrapper]")
    wrapper_path = Path.home() / ".claude" / "scripts" / "todoist"
    check(
        "~/.claude/scripts/todoist exists",
        wrapper_path.exists(),
        "Run: scripts/install.sh" if not wrapper_path.exists() else ""
    )
    if wrapper_path.exists():
        check(
            "wrapper is executable",
            wrapper_path.stat().st_mode & 0o111,
            "Run: chmod +x ~/.claude/scripts/todoist"
        )

    # PATH
    print("\n[PATH]")
    scripts_in_path = any(
        "/.claude/scripts" in p for p in os.environ.get("PATH", "").split(":")
    )
    check(
        "~/.claude/scripts in PATH",
        scripts_in_path,
        'Add to ~/.zshrc: export PATH="$HOME/.claude/scripts:$PATH"'
    )

    # Auth
    print("\n[Authentication]")
    from todoist_auth import get_auth_status
    status = get_auth_status()
    check(
        "Todoist authenticated",
        status["authenticated"],
        status["message"] if not status["authenticated"] else ""
    )

    # Network (only if auth passed)
    if status["authenticated"]:
        print("\n[Network]")
        try:
            api = get_api()
            list(api.get_projects())[:1]  # Just fetch first page
            check("API connection", True)
        except Exception as e:
            check("API connection", False, str(e)[:60])

    # Summary
    print(f"\n{'─' * 40}")
    total = checks_passed + checks_failed
    if checks_failed == 0:
        print(f"All {total} checks passed. Setup looks good!")
    else:
        print(f"{checks_passed}/{total} checks passed, {checks_failed} failed.")
        sys.exit(1)


def cmd_version(args):
    """Show version and commit info."""
    from pathlib import Path

    # Try to get git commit
    script_dir = Path(__file__).parent.parent
    commit = "unknown"
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, check=True,
            cwd=script_dir
        )
        commit = result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Try to get commit date
    commit_date = ""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%cs"],
            capture_output=True, text=True, check=True,
            cwd=script_dir
        )
        commit_date = f" ({result.stdout.strip()})"
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    print(f"todoist-gtd {commit}{commit_date}")
    print(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    print(f"Script: {Path(__file__).resolve()}")


def main():
    parser = argparse.ArgumentParser(
        description="Todoist CLI - MCP-free interface using official Python SDK",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Auth command
    p = subparsers.add_parser("auth", help="Authenticate with Todoist (OAuth)")
    p.add_argument("--manual", action="store_true", help="Use manual mode (paste redirect URL)")
    p.add_argument("--code", help="Authorization code or redirect URL (for non-interactive manual mode)")
    p.add_argument("--status", action="store_true", help="Check authentication status")

    # Natural command names (primary)
    subparsers.add_parser("projects", help="List all projects")

    p = subparsers.add_parser("sections", help="List sections")
    p.add_argument("--project-id", help="Filter by project ID")
    p.add_argument("--project", help="Filter by project name (e.g., 'Desired Outcomes Q4')")

    p = subparsers.add_parser("tasks", help="List tasks")
    p.add_argument("--project-id", help="Filter by project ID")
    p.add_argument("--project", help="Filter by project name (e.g., '@Wait')")
    p.add_argument("--section-id", help="Filter by section ID")
    p.add_argument("--section", help="Filter by section name (requires --project)")
    p.add_argument("--label", help="Filter by label")
    p.add_argument("--assignee", help="Filter by assignee name (requires --project or --project-id)")
    p.add_argument("--created-before", help="Filter by creation date (YYYY-MM-DD)")
    p.add_argument("--older-than", help="Filter by age (e.g., '30d', '2w', '3m')")
    p.add_argument("--include-section-name", action="store_true", help="Include section name in output")

    p = subparsers.add_parser("task", help="Get a single task")
    p.add_argument("id", help="Task ID")

    p = subparsers.add_parser("filter", help="Filter tasks using Todoist filter syntax")
    p.add_argument("query", help="Filter query (e.g., 'today', 'overdue', '#project')")

    p = subparsers.add_parser("done", help="Complete a task")
    p.add_argument("id", help="Task ID")

    p = subparsers.add_parser("add", help="Create a new task")
    p.add_argument("content", help="Task content/title")
    p.add_argument("--description", help="Task description")
    p.add_argument("--project-id", help="Project ID")
    p.add_argument("--project", help="Project by name (e.g., '@Work', 'Someday/Maybe')")
    p.add_argument("--section-id", help="Section ID")
    p.add_argument("--section", help="Section by name (e.g., 'Now') - requires --project")
    p.add_argument("--parent-id", help="Parent task ID (for subtasks)")
    p.add_argument("--labels", help="Comma-separated labels")
    p.add_argument("--priority", type=int, choices=[1, 2, 3, 4], help="Priority (1=normal, 4=urgent)")
    p.add_argument("--due", help="Due date in natural language")

    p = subparsers.add_parser("update", help="Update an existing task")
    p.add_argument("id", help="Task ID")
    p.add_argument("--content", help="New task content/title")
    p.add_argument("--description", help="New description (use '' to clear)")
    p.add_argument("--project-id", help="Move to project ID")
    p.add_argument("--project", help="Move to project by name (e.g., '@Ping')")
    p.add_argument("--section-id", help="Move to section ID")
    p.add_argument("--section", help="Move to section by name (e.g., 'Now')")
    p.add_argument("--labels", help="New comma-separated labels (replaces existing)")
    p.add_argument("--priority", type=int, choices=[1, 2, 3, 4], help="Priority (1=normal, 4=urgent)")
    p.add_argument("--due", help="Due date in natural language")

    p = subparsers.add_parser("comments", help="Get comments")
    p.add_argument("--task-id", help="Task ID")
    p.add_argument("--project-id", help="Project ID")

    p = subparsers.add_parser("collaborators", help="Get project collaborators")
    p.add_argument("--project-id", required=True, help="Project ID")

    p = subparsers.add_parser("add-section", help="Create a new section (outcome)")
    p.add_argument("name", help="Section name")
    p.add_argument("--project-id", help="Project ID")
    p.add_argument("--project", help="Project by name (e.g., 'Desired Outcomes Q1')")

    # Utility commands
    subparsers.add_parser("doctor", help="Check CLI setup and diagnose issues")
    subparsers.add_parser("version", help="Show version and commit info")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Dispatch to command handler
    commands = {
        "auth": cmd_auth,
        "projects": cmd_get_projects,
        "sections": cmd_get_sections,
        "tasks": cmd_get_tasks,
        "task": cmd_get_task,
        "filter": cmd_filter_tasks,
        "done": cmd_complete_task,
        "add": cmd_add_task,
        "update": cmd_update_task,
        "add-section": cmd_add_section,
        "comments": cmd_get_comments,
        "collaborators": cmd_get_collaborators,
        "doctor": cmd_doctor,
        "version": cmd_version,
    }

    handler = commands.get(args.command)
    if handler:
        try:
            handler(args)
        except Exception as e:
            # Catch network errors globally
            error_name = type(e).__name__
            error_str = str(e).lower()

            # httpx timeout errors
            if "timeout" in error_name.lower() or "timeout" in error_str:
                print(f"Error: Request timed out after {DEFAULT_TIMEOUT}s", file=sys.stderr)
                print("Check your network connection or try again.", file=sys.stderr)
                sys.exit(1)

            # httpx connection errors
            if "connect" in error_name.lower() or "connection" in error_str:
                print(f"Error: Could not connect to Todoist", file=sys.stderr)
                print("Check your network connection.", file=sys.stderr)
                sys.exit(1)

            # Re-raise unknown errors
            raise
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
