"""Tests for WorkspaceManager."""

import pytest
from unittest.mock import MagicMock, patch


class TestWorkspaceManager:
    def test_create_workspace(self):
        from agent_on_call.workspace import WorkspaceManager

        with patch("agent_on_call.workspace.docker") as mock_docker:
            mock_client = MagicMock()
            mock_docker.from_env.return_value = mock_client
            mock_container = MagicMock()
            mock_container.id = "abc123"
            mock_client.containers.run.return_value = mock_container

            mgr = WorkspaceManager()
            result = mgr.create_workspace("test-project")

            assert result == "abc123"
            mock_client.containers.run.assert_called_once()
            call_kwargs = mock_client.containers.run.call_args
            assert call_kwargs[0][0] == "aoc-workspace-dev"
            assert "aoc-workspace-test-project" in str(call_kwargs)

    def test_exec_command(self):
        from agent_on_call.workspace import WorkspaceManager

        with patch("agent_on_call.workspace.docker") as mock_docker:
            mock_client = MagicMock()
            mock_docker.from_env.return_value = mock_client
            mock_container = MagicMock()
            mock_container.status = "running"
            mock_container.exec_run.return_value = MagicMock(exit_code=0, output=(b"hello world\n", b""))

            mgr = WorkspaceManager()
            mgr._active_container = mock_container
            mgr._workspace_name = "test"

            exit_code, output = mgr.exec_command("echo hello world")
            assert exit_code == 0
            assert "hello world" in output

    def test_exec_command_no_workspace_raises(self):
        from agent_on_call.workspace import WorkspaceManager

        with patch("agent_on_call.workspace.docker") as mock_docker:
            mock_docker.from_env.return_value = MagicMock()
            mgr = WorkspaceManager()

            with pytest.raises(RuntimeError, match="No active workspace"):
                mgr.exec_command("ls")

    def test_list_workspaces(self):
        from agent_on_call.workspace import WorkspaceManager

        with patch("agent_on_call.workspace.docker") as mock_docker:
            mock_client = MagicMock()
            mock_docker.from_env.return_value = mock_client
            mock_c1 = MagicMock(name="aoc-ws-project1", status="running", short_id="abc")
            mock_c1.name = "aoc-ws-project1"
            mock_c2 = MagicMock(name="aoc-ws-project2", status="exited", short_id="def")
            mock_c2.name = "aoc-ws-project2"
            mock_client.containers.list.return_value = [mock_c1, mock_c2]

            mgr = WorkspaceManager()
            workspaces = mgr.list_workspaces()

            assert len(workspaces) == 2
            assert workspaces[0]["name"] == "project1"
            assert workspaces[1]["status"] == "exited"

    def test_read_file(self):
        from agent_on_call.workspace import WorkspaceManager

        with patch("agent_on_call.workspace.docker") as mock_docker:
            mock_client = MagicMock()
            mock_docker.from_env.return_value = mock_client
            mock_container = MagicMock()
            mock_container.status = "running"
            mock_container.exec_run.return_value = MagicMock(exit_code=0, output=(b"file content here", b""))

            mgr = WorkspaceManager()
            mgr._active_container = mock_container
            mgr._workspace_name = "test"

            content = mgr.read_file("/workspace/test.txt")
            assert content == "file content here"

    def test_get_active_workspace(self):
        from agent_on_call.workspace import WorkspaceManager

        with patch("agent_on_call.workspace.docker") as mock_docker:
            mock_docker.from_env.return_value = MagicMock()
            mgr = WorkspaceManager()
            assert mgr.get_active_workspace() is None

            mgr._workspace_name = "my-project"
            assert mgr.get_active_workspace() == "my-project"
