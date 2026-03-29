"""Tests for WorkspaceManager."""

import pytest
from unittest.mock import MagicMock, patch


class TestGitCredentialHelpers:
    def test_inject_credentials_https_github(self):
        from agent_on_call.workspace import inject_git_credentials

        url = "https://github.com/user/repo.git"
        result = inject_git_credentials(url, "ghp_test123")
        assert result == "https://ghp_test123@github.com/user/repo.git"

    def test_inject_credentials_https_no_git_suffix(self):
        from agent_on_call.workspace import inject_git_credentials

        url = "https://github.com/user/repo"
        result = inject_git_credentials(url, "ghp_test123")
        assert result == "https://ghp_test123@github.com/user/repo"

    def test_inject_credentials_https_gitlab(self):
        from agent_on_call.workspace import inject_git_credentials

        url = "https://gitlab.com/user/repo.git"
        result = inject_git_credentials(url, "glpat_test123")
        assert result == "https://glpat_test123@gitlab.com/user/repo.git"

    def test_inject_credentials_ssh_url_unchanged(self):
        from agent_on_call.workspace import inject_git_credentials

        url = "git@github.com:user/repo.git"
        result = inject_git_credentials(url, "ghp_test123")
        assert result == url  # SSH URLs not modified

    def test_inject_credentials_no_token(self):
        from agent_on_call.workspace import inject_git_credentials

        url = "https://github.com/user/repo.git"
        result = inject_git_credentials(url, None)
        assert result == url  # No token, no change

    def test_inject_credentials_empty_token(self):
        from agent_on_call.workspace import inject_git_credentials

        url = "https://github.com/user/repo.git"
        result = inject_git_credentials(url, "")
        assert result == url  # Empty token, no change

    def test_sanitize_output_replaces_token(self):
        from agent_on_call.workspace import sanitize_git_output

        output = "Cloning into 'repo'... remote: https://ghp_secret123@github.com/user/repo.git"
        result = sanitize_git_output(output, "ghp_secret123")
        assert "ghp_secret123" not in result
        assert "***" in result

    def test_sanitize_output_no_token(self):
        from agent_on_call.workspace import sanitize_git_output

        output = "Cloning into 'repo'..."
        result = sanitize_git_output(output, None)
        assert result == output

    def test_sanitize_output_empty_token(self):
        from agent_on_call.workspace import sanitize_git_output

        output = "Cloning into 'repo'..."
        result = sanitize_git_output(output, "")
        assert result == output

    def test_sanitize_output_multiple_occurrences(self):
        from agent_on_call.workspace import sanitize_git_output

        output = "token=ghp_abc123 remote=ghp_abc123"
        result = sanitize_git_output(output, "ghp_abc123")
        assert "ghp_abc123" not in result
        assert result.count("***") == 2


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

    def test_exec_command_returns_three_tuple(self):
        from agent_on_call.workspace import WorkspaceManager

        with patch("agent_on_call.workspace.docker") as mock_docker:
            mock_client = MagicMock()
            mock_docker.from_env.return_value = mock_client
            mock_container = MagicMock()
            mock_container.status = "running"
            mock_container.exec_run.return_value = MagicMock(
                exit_code=0, output=(b"hello world\n", b"some warning\n")
            )

            mgr = WorkspaceManager()
            mgr._active_container = mock_container
            mgr._workspace_name = "test"

            exit_code, stdout, stderr = mgr.exec_command("echo hello world")
            assert exit_code == 0
            assert "hello world" in stdout
            assert "some warning" in stderr

    def test_exec_command_empty_output(self):
        from agent_on_call.workspace import WorkspaceManager

        with patch("agent_on_call.workspace.docker") as mock_docker:
            mock_client = MagicMock()
            mock_docker.from_env.return_value = mock_client
            mock_container = MagicMock()
            mock_container.status = "running"
            mock_container.exec_run.return_value = MagicMock(
                exit_code=0, output=(None, None)
            )

            mgr = WorkspaceManager()
            mgr._active_container = mock_container
            mgr._workspace_name = "test"

            exit_code, stdout, stderr = mgr.exec_command("true")
            assert exit_code == 0
            assert stdout == ""
            assert stderr == ""

    def test_exec_command_nonzero_exit(self):
        from agent_on_call.workspace import WorkspaceManager

        with patch("agent_on_call.workspace.docker") as mock_docker:
            mock_client = MagicMock()
            mock_docker.from_env.return_value = mock_client
            mock_container = MagicMock()
            mock_container.status = "running"
            mock_container.exec_run.return_value = MagicMock(
                exit_code=1, output=(b"", b"command not found\n")
            )

            mgr = WorkspaceManager()
            mgr._active_container = mock_container
            mgr._workspace_name = "test"

            exit_code, stdout, stderr = mgr.exec_command("badcmd")
            assert exit_code == 1
            assert "command not found" in stderr

    def test_exec_command_no_workspace_raises(self):
        from agent_on_call.workspace import WorkspaceManager

        with patch("agent_on_call.workspace.docker") as mock_docker:
            mock_docker.from_env.return_value = MagicMock()
            mgr = WorkspaceManager()

            with pytest.raises(RuntimeError, match="No active workspace"):
                mgr.exec_command("ls")

    def test_exec_command_timeout(self):
        import time
        from agent_on_call.workspace import WorkspaceManager

        with patch("agent_on_call.workspace.docker") as mock_docker:
            mock_client = MagicMock()
            mock_docker.from_env.return_value = mock_client
            mock_container = MagicMock()
            mock_container.status = "running"

            def slow_exec(*args, **kwargs):
                time.sleep(5)
                return MagicMock(exit_code=0, output=(b"done", b""))

            mock_container.exec_run.side_effect = slow_exec

            mgr = WorkspaceManager()
            mgr._active_container = mock_container
            mgr._workspace_name = "test"

            with pytest.raises(TimeoutError, match="timed out"):
                mgr.exec_command("sleep 60", timeout=1)

    def test_exec_command_restarts_stopped_container(self):
        from agent_on_call.workspace import WorkspaceManager

        with patch("agent_on_call.workspace.docker") as mock_docker:
            mock_client = MagicMock()
            mock_docker.from_env.return_value = mock_client
            mock_container = MagicMock()
            mock_container.status = "exited"

            def reload_side_effect():
                # After start() is called, status changes to running
                if mock_container.start.called:
                    mock_container.status = "running"

            mock_container.reload.side_effect = reload_side_effect
            mock_container.exec_run.return_value = MagicMock(
                exit_code=0, output=(b"output", b"")
            )

            mgr = WorkspaceManager()
            mgr._active_container = mock_container
            mgr._workspace_name = "test"

            exit_code, stdout, stderr = mgr.exec_command("ls")
            assert exit_code == 0
            mock_container.start.assert_called_once()

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

    def test_read_file_not_found(self):
        from agent_on_call.workspace import WorkspaceManager

        with patch("agent_on_call.workspace.docker") as mock_docker:
            mock_client = MagicMock()
            mock_docker.from_env.return_value = mock_client
            mock_container = MagicMock()
            mock_container.status = "running"
            mock_container.exec_run.return_value = MagicMock(
                exit_code=1, output=(b"", b"No such file or directory")
            )

            mgr = WorkspaceManager()
            mgr._active_container = mock_container
            mgr._workspace_name = "test"

            with pytest.raises(FileNotFoundError):
                mgr.read_file("/workspace/nonexistent.txt")

    def test_get_active_workspace(self):
        from agent_on_call.workspace import WorkspaceManager

        with patch("agent_on_call.workspace.docker") as mock_docker:
            mock_docker.from_env.return_value = MagicMock()
            mgr = WorkspaceManager()
            assert mgr.get_active_workspace() is None

            mgr._workspace_name = "my-project"
            assert mgr.get_active_workspace() == "my-project"
