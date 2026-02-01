"""
Shared utilities for Todoist CLI tools.

Provides common functions used across todoist.py and flatten-subtasks.py:
- API client with timeout and retry
- Pagination helpers
- Project/section resolution
- Object serialization
"""

import sys
import time
from typing import Any, Callable

# Lazy imports to allow --help without SDK installed
TodoistAPI = None

# Configuration
DEFAULT_TIMEOUT = 30  # seconds
RATE_LIMIT_DELAY = 0.2  # seconds between API calls
RATE_LIMIT_RETRY_DELAY = 5  # seconds to wait after 429
MAX_RETRIES = 3


def get_api():
    """
    Get authenticated TodoistAPI instance with timeout.

    Uses requests.Session with timeout adapter for reliability.
    Note: Don't use httpx - SDK expects requests.Session and breaks with httpx
    (complete_task fails with 'Response' has no 'ok').
    """
    global TodoistAPI
    if TodoistAPI is None:
        try:
            from todoist_api_python.api import TodoistAPI as API
            TodoistAPI = API
        except ImportError:
            print("Error: todoist-api-python not installed", file=sys.stderr)
            print("\nInstall with: pip install todoist-api-python", file=sys.stderr)
            sys.exit(1)

    from todoist_secrets import get_token
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

    token = get_token()

    # Configure session with timeout and retry
    session = requests.Session()
    retry_strategy = Retry(
        total=MAX_RETRIES,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)

    # Set default timeout for all requests
    session.request = _timeout_wrapper(session.request, DEFAULT_TIMEOUT)

    return TodoistAPI(token, session=session)


def _timeout_wrapper(func: Callable, timeout: int) -> Callable:
    """Wrap a request function to add default timeout."""
    def wrapper(*args, **kwargs):
        kwargs.setdefault('timeout', timeout)
        return func(*args, **kwargs)
    return wrapper


def collect_paginated(iterator) -> list:
    """Collect all items from a paginated SDK iterator."""
    items = []
    for batch in iterator:
        items.extend(batch)
    return items


def to_dict(obj: Any) -> dict:
    """Convert SDK object to dict for JSON output."""
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()
    if hasattr(obj, '__dict__'):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
    return obj


def resolve_project(api, name_or_id: str) -> str:
    """
    Resolve a project name to ID.

    Returns project ID string. Exits with error if not found.
    """
    projects = collect_paginated(api.get_projects())
    name_lower = name_or_id.lower()

    # Try name lookup
    for p in projects:
        if p.name.lower() == name_lower:
            return p.id

    # Try ID lookup
    for p in projects:
        if p.id == name_or_id:
            return p.id

    # Not found - show available projects
    available = sorted([p.name for p in projects])
    print(f"Error: Project '{name_or_id}' not found", file=sys.stderr)
    print(f"Available projects: {', '.join(available[:10])}", file=sys.stderr)
    if len(available) > 10:
        print(f"  ...and {len(available) - 10} more", file=sys.stderr)
    print("\n⚠️  STOP: Load the todoist-gtd skill before using this CLI!", file=sys.stderr)
    sys.exit(1)


def resolve_project_with_name(api, name_or_id: str) -> tuple[str, str]:
    """
    Resolve a project name to (ID, name) tuple.

    Returns (project_id, project_name). Exits with error if not found.
    """
    projects = collect_paginated(api.get_projects())
    name_lower = name_or_id.lower()

    # Try name lookup
    for p in projects:
        if p.name.lower() == name_lower:
            return p.id, p.name

    # Try ID lookup
    for p in projects:
        if p.id == name_or_id:
            return p.id, p.name

    print(f"Error: Project '{name_or_id}' not found", file=sys.stderr)
    sys.exit(1)


def resolve_section(api, project_id: str, name_or_id: str) -> str:
    """
    Resolve a section name to ID within a project.

    Returns section ID string. Exits with error if not found.
    """
    sections = collect_paginated(api.get_sections(project_id=project_id))
    name_lower = name_or_id.lower()

    # Try name lookup
    for s in sections:
        if s.name.lower() == name_lower:
            return s.id

    # Try ID lookup
    for s in sections:
        if s.id == name_or_id:
            return s.id

    # Not found - show available sections
    available = [s.name for s in sections]
    print(f"Error: Section '{name_or_id}' not found in project", file=sys.stderr)
    if available:
        print(f"Available sections: {', '.join(available)}", file=sys.stderr)
    else:
        print("This project has no sections.", file=sys.stderr)
    print("\n⚠️  STOP: Load the todoist-gtd skill before using this CLI!", file=sys.stderr)
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


def api_call_with_retry(func: Callable, *args, **kwargs) -> Any:
    """
    Execute API call with rate limit handling and retry.

    Adds a small delay before each call to avoid hitting rate limits,
    and retries on 429 errors.
    """
    for attempt in range(MAX_RETRIES):
        try:
            time.sleep(RATE_LIMIT_DELAY)
            return func(*args, **kwargs)
        except Exception as e:
            error_str = str(e).lower()
            if "429" in str(e) or "rate limit" in error_str:
                if attempt < MAX_RETRIES - 1:
                    print(f"  ⏳ Rate limited, waiting {RATE_LIMIT_RETRY_DELAY}s...",
                          file=sys.stderr)
                    time.sleep(RATE_LIMIT_RETRY_DELAY)
                    continue
            raise
    raise Exception("Max retries exceeded")


def handle_task_not_found(e: Exception, task_id: str):
    """Handle task not found errors with clean message."""
    error_str = str(e).lower()
    # Todoist returns 400 for invalid IDs, 404 for valid-format but missing
    if "404" in error_str or "not found" in error_str or "400" in error_str:
        print(f"Error: Task '{task_id}' not found or invalid", file=sys.stderr)
        sys.exit(1)
    # Re-raise if it's a different error
    raise
