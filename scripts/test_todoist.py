#!/usr/bin/env python3
"""
Tests for todoist-gtd CLI.

These tests verify critical paths without mocking the API.
They create real tasks and clean them up after.

Run with: python -m pytest test_todoist.py -v
Or: python test_todoist.py (runs basic smoke tests)
"""

import json
import subprocess
import sys
import time
from pathlib import Path

# Test configuration
TEST_PROJECT = "Inbox"  # Use Inbox for tests (always exists)
TEST_PREFIX = "TEST-TODOIST-GTD-"  # Prefix for test tasks


def run_cli(*args, check=True):
    """Run todoist CLI and return parsed JSON output."""
    cmd = [sys.executable, "todoist.py"] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True, check=check)
    if result.returncode != 0 and check:
        print(f"STDERR: {result.stderr}", file=sys.stderr)
        raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
    if result.stdout.strip():
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return result.stdout
    return None


def cleanup_test_tasks():
    """Delete any leftover test tasks."""
    try:
        tasks = run_cli("tasks", "--project", TEST_PROJECT)
        for task in tasks:
            if task.get("content", "").startswith(TEST_PREFIX):
                run_cli("delete", task["id"], check=False)
                time.sleep(0.2)
    except Exception as e:
        print(f"Cleanup warning: {e}", file=sys.stderr)


class TestCommon:
    """Test todoist_common module."""

    def test_imports(self):
        """Verify common module imports correctly."""
        from todoist_common import (
            get_api,
            collect_paginated,
            to_dict,
            resolve_project,
            resolve_section,
            api_call_with_retry,
            DEFAULT_TIMEOUT,
        )
        assert DEFAULT_TIMEOUT == 30

    def test_get_api(self):
        """Verify API client can be created."""
        from todoist_common import get_api
        api = get_api()
        assert api is not None


class TestCLI:
    """Test CLI commands."""

    def test_version(self):
        """Test version command."""
        result = run_cli("version")
        assert "todoist-gtd" in result

    def test_projects(self):
        """Test projects command returns list."""
        projects = run_cli("projects")
        assert isinstance(projects, list)
        assert len(projects) > 0
        assert "id" in projects[0]
        assert "name" in projects[0]

    def test_sections(self):
        """Test sections command."""
        sections = run_cli("sections")
        assert isinstance(sections, list)

    def test_tasks(self):
        """Test tasks command."""
        tasks = run_cli("tasks", "--project", TEST_PROJECT)
        assert isinstance(tasks, list)


class TestTaskLifecycle:
    """Test task create/update/complete/delete lifecycle."""

    def setup_method(self):
        """Clean up before each test."""
        cleanup_test_tasks()

    def teardown_method(self):
        """Clean up after each test."""
        cleanup_test_tasks()

    def test_add_task(self):
        """Test adding a task."""
        content = f"{TEST_PREFIX}add-test"
        task = run_cli("add", content, "--project", TEST_PROJECT)

        assert task["content"] == content
        assert "id" in task

        # Cleanup
        run_cli("delete", task["id"])

    def test_add_task_with_description(self):
        """Test adding a task with description."""
        content = f"{TEST_PREFIX}desc-test"
        description = "This is a test description"
        task = run_cli("add", content, "--project", TEST_PROJECT, "--description", description)

        assert task["content"] == content
        assert task["description"] == description

        # Cleanup
        run_cli("delete", task["id"])

    def test_update_task(self):
        """Test updating a task."""
        content = f"{TEST_PREFIX}update-test"
        task = run_cli("add", content, "--project", TEST_PROJECT)

        new_content = f"{TEST_PREFIX}updated"
        updated = run_cli("update", task["id"], "--content", new_content)

        assert updated["content"] == new_content

        # Cleanup
        run_cli("delete", task["id"])

    def test_complete_task(self):
        """Test completing a task."""
        content = f"{TEST_PREFIX}complete-test"
        task = run_cli("add", content, "--project", TEST_PROJECT)

        result = run_cli("done", task["id"])
        assert result["success"] is True

        # Cleanup - delete completed task
        run_cli("delete", task["id"])

    def test_delete_task(self):
        """Test deleting a task."""
        content = f"{TEST_PREFIX}delete-test"
        task = run_cli("add", content, "--project", TEST_PROJECT)

        result = run_cli("delete", task["id"])
        assert result["success"] is True

    def test_get_single_task(self):
        """Test getting a single task."""
        content = f"{TEST_PREFIX}get-test"
        created = run_cli("add", content, "--project", TEST_PROJECT)

        fetched = run_cli("task", created["id"])
        assert fetched["content"] == content
        assert fetched["id"] == created["id"]

        # Cleanup
        run_cli("delete", created["id"])


class TestCompleted:
    """Test completed tasks commands."""

    def test_completed_list(self):
        """Test listing completed tasks."""
        # Create and complete a task
        content = f"{TEST_PREFIX}completed-list-test"
        task = run_cli("add", content, "--project", TEST_PROJECT)
        run_cli("done", task["id"])
        time.sleep(0.5)  # Wait for completion to register

        # List completed
        completed = run_cli("completed", "--since", "2020-01-01")
        assert isinstance(completed, list)

        # Cleanup
        run_cli("delete", task["id"])


class TestFlattenSubtasks:
    """Test flatten-subtasks script."""

    def test_help(self):
        """Test flatten-subtasks help."""
        cmd = [sys.executable, "flatten-subtasks.py", "--help"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0
        assert "Flatten subtasks" in result.stdout

    def test_list_backups(self):
        """Test list-backups command."""
        cmd = [sys.executable, "flatten-subtasks.py", "--list-backups"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0


def run_smoke_tests():
    """Run basic smoke tests without pytest."""
    print("Running smoke tests...\n")

    tests = [
        ("Import common module", lambda: __import__("todoist_common")),
        ("Get API client", lambda: __import__("todoist_common").get_api()),
        ("List projects", lambda: run_cli("projects")),
        ("CLI version", lambda: run_cli("version")),
    ]

    passed = 0
    failed = 0

    for name, test_fn in tests:
        try:
            test_fn()
            print(f"  ✓ {name}")
            passed += 1
        except Exception as e:
            print(f"  ✗ {name}: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    # When run directly, do smoke tests
    success = run_smoke_tests()
    sys.exit(0 if success else 1)
