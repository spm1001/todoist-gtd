"""Tests for todoist-gtd CLI commands."""

import json
import sys
from io import StringIO
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


# --- Fixtures ---


def make_task(task_id="t1", content="Test task", assignee_id=None, project_id="p1",
              comment_count=0, created_at="2026-01-01T00:00:00Z", section_id=None):
    """Create a mock Task object matching the SDK's interface."""
    task = SimpleNamespace(
        id=task_id,
        content=content,
        assignee_id=assignee_id,
        project_id=project_id,
        comment_count=comment_count,
        created_at=created_at,
        section_id=section_id,
    )
    task.to_dict = lambda: {
        "id": task.id,
        "content": task.content,
        "assignee_id": task.assignee_id,
        "project_id": task.project_id,
        "comment_count": task.comment_count,
        "created_at": task.created_at,
        "section_id": task.section_id,
    }
    return task


def make_collaborator(cid, name, email=""):
    return SimpleNamespace(id=cid, name=name, email=email)


def make_comment(content="", attachment=None):
    comment = SimpleNamespace(content=content, attachment=attachment)
    comment.to_dict = lambda: {"content": comment.content, "attachment": comment.attachment}
    return comment


def paginated(*items):
    """Simulate the SDK's paginated iterator (yields batches)."""
    yield list(items)


# --- get_current_user ---


class TestGetCurrentUser:
    @patch("todoist_gtd.token_store.get_token", return_value="test-token")
    @patch("httpx.get")
    def test_returns_user_dict(self, mock_get, mock_token):
        from todoist_gtd.common import get_current_user

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "123",
            "full_name": "Test User",
            "email": "test@example.com",
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        user = get_current_user()

        assert user["id"] == "123"
        assert user["full_name"] == "Test User"
        assert user["email"] == "test@example.com"
        mock_get.assert_called_once_with(
            "https://api.todoist.com/api/v1/user",
            headers={"Authorization": "Bearer test-token"},
            timeout=30,
        )

    @patch("todoist_gtd.token_store.get_token", return_value="bad-token")
    @patch("httpx.get")
    def test_raises_on_401(self, mock_get, mock_token):
        from todoist_gtd.common import get_current_user
        import httpx

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401 Unauthorized", request=MagicMock(), response=MagicMock(status_code=401)
        )
        mock_get.return_value = mock_response

        with pytest.raises(httpx.HTTPStatusError):
            get_current_user()


# --- cmd_whoami ---


class TestWhoami:
    @patch("todoist_gtd.cli.get_current_user")
    def test_human_output(self, mock_user, capsys):
        from todoist_gtd.cli import cmd_whoami

        mock_user.return_value = {
            "id": "123",
            "full_name": "Sameer Modha",
            "email": "sameer@example.com",
        }

        args = SimpleNamespace(json=False)
        cmd_whoami(args)

        out = capsys.readouterr().out
        assert "Sameer Modha" in out
        assert "sameer@example.com" in out
        assert "123" in out

    @patch("todoist_gtd.cli.get_current_user")
    def test_json_output(self, mock_user, capsys):
        from todoist_gtd.cli import cmd_whoami

        mock_user.return_value = {
            "id": "123",
            "full_name": "Sameer Modha",
            "email": "sameer@example.com",
        }

        args = SimpleNamespace(json=True)
        cmd_whoami(args)

        out = json.loads(capsys.readouterr().out)
        assert out["id"] == "123"
        assert out["full_name"] == "Sameer Modha"


# --- Assignee enrichment ---


class TestAssigneeEnrichment:
    @patch("todoist_gtd.cli.get_api")
    @patch("todoist_gtd.cli.collect_paginated")
    def test_assignee_name_resolved_in_task_output(self, mock_collect, mock_api, capsys):
        from todoist_gtd.cli import cmd_get_task

        task = make_task(assignee_id="456", project_id="p1")
        collabs = [make_collaborator("456", "Lauren Thomas")]

        def side_effect(iterator):
            # Return different values based on what's being paginated
            return list(iterator)

        mock_api_instance = MagicMock()
        mock_api.return_value = mock_api_instance
        mock_api_instance.get_task.return_value = task

        # First call: get_collaborators, Second call: get_comments
        mock_collect.side_effect = [
            collabs,    # collaborators
            [],         # comments
        ]

        args = SimpleNamespace(id="t1")
        cmd_get_task(args)

        out = json.loads(capsys.readouterr().out)
        assert out["assignee_name"] == "Lauren Thomas"

    @patch("todoist_gtd.cli.get_api")
    @patch("todoist_gtd.cli.collect_paginated")
    def test_null_assignee_gives_null_name(self, mock_collect, mock_api, capsys):
        from todoist_gtd.cli import cmd_get_task

        task = make_task(assignee_id=None, project_id="p1")

        mock_api_instance = MagicMock()
        mock_api.return_value = mock_api_instance
        mock_api_instance.get_task.return_value = task

        mock_collect.side_effect = [
            [],  # comments (no collaborator call since assignee_id is None)
        ]

        args = SimpleNamespace(id="t1")
        cmd_get_task(args)

        out = json.loads(capsys.readouterr().out)
        assert out["assignee_name"] is None


# --- Auto-filter on shared projects ---


class TestAutoFilter:
    @patch("todoist_gtd.cli.get_current_user")
    @patch("todoist_gtd.cli.get_api")
    @patch("todoist_gtd.cli.collect_paginated")
    @patch("todoist_gtd.cli.resolve_project")
    def test_shared_project_filters_to_my_tasks(self, mock_resolve, mock_collect,
                                                  mock_api, mock_user, capsys):
        from todoist_gtd.cli import cmd_get_tasks

        mock_resolve.return_value = "p1"
        mock_user.return_value = {"id": "100", "full_name": "Me"}
        mock_api.return_value = MagicMock()

        my_task = make_task("t1", "My task", assignee_id="100")
        their_task = make_task("t2", "Their task", assignee_id="200")
        unassigned = make_task("t3", "Unassigned task", assignee_id=None)
        collabs = [
            make_collaborator("100", "Me"),
            make_collaborator("200", "Them"),
        ]

        mock_collect.side_effect = [
            [my_task, their_task, unassigned],  # get_tasks
            collabs,                             # get_collaborators (once)
            [],                                  # comments for t1
            [],                                  # comments for t3
        ]

        args = SimpleNamespace(
            project="Shared", project_id=None, section=None, section_id=None,
            label=None, assignee=None, team=False,
            created_before=None, older_than=None, include_section_name=False,
        )
        cmd_get_tasks(args)

        out = json.loads(capsys.readouterr().out)
        contents = [t["content"] for t in out]
        assert "My task" in contents
        assert "Unassigned task" in contents
        assert "Their task" not in contents

    @patch("todoist_gtd.cli.get_api")
    @patch("todoist_gtd.cli.collect_paginated")
    @patch("todoist_gtd.cli.resolve_project")
    def test_team_flag_shows_all(self, mock_resolve, mock_collect, mock_api, capsys):
        from todoist_gtd.cli import cmd_get_tasks

        mock_resolve.return_value = "p1"
        mock_api.return_value = MagicMock()

        my_task = make_task("t1", "My task", assignee_id="100")
        their_task = make_task("t2", "Their task", assignee_id="200")
        collabs = [
            make_collaborator("100", "Me"),
            make_collaborator("200", "Them"),
        ]

        mock_collect.side_effect = [
            [my_task, their_task],  # get_tasks
            collabs,                # get_collaborators
            [],                     # comments for t1
            [],                     # comments for t2
        ]

        args = SimpleNamespace(
            project="Shared", project_id=None, section=None, section_id=None,
            label=None, assignee=None, team=True,
            created_before=None, older_than=None, include_section_name=False,
        )
        cmd_get_tasks(args)

        out = json.loads(capsys.readouterr().out)
        assert len(out) == 2

    @patch("todoist_gtd.cli.get_api")
    @patch("todoist_gtd.cli.collect_paginated")
    @patch("todoist_gtd.cli.resolve_project")
    def test_personal_project_no_filter(self, mock_resolve, mock_collect, mock_api, capsys):
        from todoist_gtd.cli import cmd_get_tasks

        mock_resolve.return_value = "p1"
        mock_api.return_value = MagicMock()

        tasks = [make_task("t1", "Task A"), make_task("t2", "Task B")]

        mock_collect.side_effect = [
            tasks,  # get_tasks
            [],     # get_collaborators (empty = personal)
            [],     # comments for t1
            [],     # comments for t2
        ]

        args = SimpleNamespace(
            project="Personal", project_id=None, section=None, section_id=None,
            label=None, assignee=None, team=False,
            created_before=None, older_than=None, include_section_name=False,
        )
        cmd_get_tasks(args)

        out = json.loads(capsys.readouterr().out)
        assert len(out) == 2


# --- Comment guard removal ---


class TestCommentGuardRemoval:
    @patch("todoist_gtd.cli.get_api")
    @patch("todoist_gtd.cli.collect_paginated")
    def test_comments_fetched_even_with_zero_comment_count(self, mock_collect, mock_api, capsys):
        from todoist_gtd.cli import cmd_get_task

        task = make_task(comment_count=0)
        attachment_comment = make_comment(
            content="",
            attachment={"file_name": "report.pdf", "file_type": "application/pdf"},
        )

        mock_api_instance = MagicMock()
        mock_api.return_value = mock_api_instance
        mock_api_instance.get_task.return_value = task

        mock_collect.side_effect = [
            [attachment_comment],  # comments fetched despite count=0
        ]

        args = SimpleNamespace(id="t1")
        cmd_get_task(args)

        out = json.loads(capsys.readouterr().out)
        assert len(out["comments"]) == 1
        assert out["comments"][0]["attachment"]["file_name"] == "report.pdf"
