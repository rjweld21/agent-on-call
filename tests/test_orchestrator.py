"""Tests for OrchestratorAgent."""

import json
import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestEmitAction:
    @pytest.mark.asyncio
    async def test_emit_action_publishes_to_data_channel(self):
        with patch("agent_on_call.orchestrator.WorkspaceManager"):
            from agent_on_call.orchestrator import OrchestratorAgent

            agent = OrchestratorAgent()
            mock_room = MagicMock()
            mock_room.local_participant.publish_data = AsyncMock()
            agent.set_room(mock_room)

            await agent._emit_action("executing", "exec_command", "Running: ls", detail="ls -la")

            mock_room.local_participant.publish_data.assert_called_once()
            call_args = mock_room.local_participant.publish_data.call_args
            payload = json.loads(call_args[0][0].decode())
            assert payload["type"] == "agent_action"
            assert payload["action"]["kind"] == "executing"
            assert payload["action"]["tool"] == "exec_command"
            assert payload["action"]["summary"] == "Running: ls"
            assert payload["action"]["detail"] == "ls -la"
            assert payload["action"]["status"] == "started"
            assert "id" in payload["action"]
            assert "timestamp" in payload["action"]

    @pytest.mark.asyncio
    async def test_emit_action_noop_when_no_room(self):
        with patch("agent_on_call.orchestrator.WorkspaceManager"):
            from agent_on_call.orchestrator import OrchestratorAgent

            agent = OrchestratorAgent()
            # No set_room call — _room is None
            # Should not raise
            await agent._emit_action("executing", "exec_command", "test")

    @pytest.mark.asyncio
    async def test_emit_action_handles_publish_error(self):
        with patch("agent_on_call.orchestrator.WorkspaceManager"):
            from agent_on_call.orchestrator import OrchestratorAgent

            agent = OrchestratorAgent()
            mock_room = MagicMock()
            mock_room.local_participant.publish_data = AsyncMock(side_effect=RuntimeError("publish failed"))
            agent.set_room(mock_room)

            # Should not raise — error is caught and logged
            await agent._emit_action("executing", "exec_command", "test")

    @pytest.mark.asyncio
    async def test_exec_command_emits_started_and_completed(self):
        with patch("agent_on_call.orchestrator.WorkspaceManager") as MockWS:
            mock_ws = MagicMock()
            mock_ws.exec_command.return_value = (0, "hello", "")
            MockWS.return_value = mock_ws

            from agent_on_call.orchestrator import OrchestratorAgent

            agent = OrchestratorAgent()
            mock_room = MagicMock()
            mock_room.local_participant.publish_data = AsyncMock()
            agent.set_room(mock_room)

            ctx = MagicMock()
            await agent.exec_command(ctx, command="echo hello")

            # Should have emitted at least 2 actions: started and completed
            calls = mock_room.local_participant.publish_data.call_args_list
            assert len(calls) >= 2
            first_payload = json.loads(calls[0][0][0].decode())
            assert first_payload["action"]["status"] == "started"
            last_payload = json.loads(calls[-1][0][0].decode())
            assert last_payload["action"]["status"] == "completed"


class TestOrchestratorAgent:
    def test_orchestrator_has_instructions(self):
        with patch("agent_on_call.orchestrator.WorkspaceManager"):
            from agent_on_call.orchestrator import OrchestratorAgent

            agent = OrchestratorAgent()
            assert "orchestrator" in agent.instructions.lower()

    def test_orchestrator_has_guidance_queue(self):
        with patch("agent_on_call.orchestrator.WorkspaceManager"):
            from agent_on_call.orchestrator import OrchestratorAgent

            agent = OrchestratorAgent()
            assert hasattr(agent, "guidance_queue")

    def test_orchestrator_has_workspace_manager(self):
        with patch("agent_on_call.orchestrator.WorkspaceManager"):
            from agent_on_call.orchestrator import OrchestratorAgent

            agent = OrchestratorAgent()
            assert hasattr(agent, "_workspace")

    def test_orchestrator_has_exec_command_tool(self):
        with patch("agent_on_call.orchestrator.WorkspaceManager"):
            from agent_on_call.orchestrator import OrchestratorAgent

            agent = OrchestratorAgent()
            assert hasattr(agent, "exec_command")

    def test_orchestrator_no_run_command_tool(self):
        """exec_command replaces the old run_command tool."""
        with patch("agent_on_call.orchestrator.WorkspaceManager"):
            from agent_on_call.orchestrator import OrchestratorAgent

            agent = OrchestratorAgent()
            assert not hasattr(agent, "run_command")


class TestExecCommandTool:
    @pytest.mark.asyncio
    async def test_exec_command_success(self):
        with patch("agent_on_call.orchestrator.WorkspaceManager") as MockWS:
            mock_ws = MagicMock()
            mock_ws.exec_command.return_value = (0, "hello world", "")
            MockWS.return_value = mock_ws

            from agent_on_call.orchestrator import OrchestratorAgent

            agent = OrchestratorAgent()
            ctx = MagicMock()
            result = await agent.exec_command(ctx, command="echo hello world")

            assert "Exit code: 0" in result
            assert "hello world" in result
            mock_ws.exec_command.assert_called_once_with("echo hello world", timeout=30)

    @pytest.mark.asyncio
    async def test_exec_command_nonzero_exit(self):
        with patch("agent_on_call.orchestrator.WorkspaceManager") as MockWS:
            mock_ws = MagicMock()
            mock_ws.exec_command.return_value = (1, "", "command not found")
            MockWS.return_value = mock_ws

            from agent_on_call.orchestrator import OrchestratorAgent

            agent = OrchestratorAgent()
            ctx = MagicMock()
            result = await agent.exec_command(ctx, command="badcmd")

            assert "Exit code: 1" in result
            assert "command not found" in result

    @pytest.mark.asyncio
    async def test_exec_command_timeout(self):
        with patch("agent_on_call.orchestrator.WorkspaceManager") as MockWS:
            mock_ws = MagicMock()
            mock_ws.exec_command.side_effect = TimeoutError("Command timed out after 5s")
            MockWS.return_value = mock_ws

            from agent_on_call.orchestrator import OrchestratorAgent

            agent = OrchestratorAgent()
            ctx = MagicMock()
            result = await agent.exec_command(ctx, command="sleep 60", timeout=5)

            assert "timed out" in result.lower()

    @pytest.mark.asyncio
    async def test_exec_command_empty_command(self):
        with patch("agent_on_call.orchestrator.WorkspaceManager"):
            from agent_on_call.orchestrator import OrchestratorAgent

            agent = OrchestratorAgent()
            ctx = MagicMock()
            result = await agent.exec_command(ctx, command="")

            assert "empty" in result.lower()

    @pytest.mark.asyncio
    async def test_exec_command_whitespace_only(self):
        with patch("agent_on_call.orchestrator.WorkspaceManager"):
            from agent_on_call.orchestrator import OrchestratorAgent

            agent = OrchestratorAgent()
            ctx = MagicMock()
            result = await agent.exec_command(ctx, command="   ")

            assert "empty" in result.lower()

    @pytest.mark.asyncio
    async def test_exec_command_too_long(self):
        with patch("agent_on_call.orchestrator.WorkspaceManager"):
            from agent_on_call.orchestrator import OrchestratorAgent

            agent = OrchestratorAgent()
            ctx = MagicMock()
            long_cmd = "x" * 10001
            result = await agent.exec_command(ctx, command=long_cmd)

            assert "too long" in result.lower()
            assert "10000" in result

    @pytest.mark.asyncio
    async def test_exec_command_no_workspace(self):
        with patch("agent_on_call.orchestrator.WorkspaceManager") as MockWS:
            mock_ws = MagicMock()
            mock_ws.exec_command.side_effect = RuntimeError("No active workspace. Create one first.")
            MockWS.return_value = mock_ws

            from agent_on_call.orchestrator import OrchestratorAgent

            agent = OrchestratorAgent()
            ctx = MagicMock()
            result = await agent.exec_command(ctx, command="ls")

            assert "No active workspace" in result

    @pytest.mark.asyncio
    async def test_exec_command_custom_timeout(self):
        with patch("agent_on_call.orchestrator.WorkspaceManager") as MockWS:
            mock_ws = MagicMock()
            mock_ws.exec_command.return_value = (0, "done", "")
            MockWS.return_value = mock_ws

            from agent_on_call.orchestrator import OrchestratorAgent

            agent = OrchestratorAgent()
            ctx = MagicMock()
            await agent.exec_command(ctx, command="pip install", timeout=120)

            mock_ws.exec_command.assert_called_once_with("pip install", timeout=120)

    @pytest.mark.asyncio
    async def test_exec_command_truncates_long_output(self):
        with patch("agent_on_call.orchestrator.WorkspaceManager") as MockWS:
            mock_ws = MagicMock()
            long_stdout = "x" * 3000
            mock_ws.exec_command.return_value = (0, long_stdout, "")
            MockWS.return_value = mock_ws

            from agent_on_call.orchestrator import OrchestratorAgent

            agent = OrchestratorAgent()
            ctx = MagicMock()
            result = await agent.exec_command(ctx, command="big output")

            assert "truncated" in result.lower()
            assert len(result) < 3000


class TestGitCloneTool:
    @pytest.mark.asyncio
    async def test_git_clone_success(self):
        with patch("agent_on_call.orchestrator.WorkspaceManager") as MockWS:
            mock_ws = MagicMock()
            mock_ws.exec_command.return_value = (
                0,
                "Cloning into 'repo'...\ndone.",
                "",
            )
            MockWS.return_value = mock_ws

            from agent_on_call.orchestrator import OrchestratorAgent

            agent = OrchestratorAgent()
            ctx = MagicMock()
            result = await agent.git_clone(ctx, repo_url="https://github.com/user/repo.git")

            assert "cloning" in result.lower() or "done" in result.lower()
            call_cmd = mock_ws.exec_command.call_args[0][0]
            assert "git clone" in call_cmd

    @pytest.mark.asyncio
    async def test_git_clone_injects_credentials(self):
        with patch("agent_on_call.orchestrator.WorkspaceManager") as MockWS:
            mock_ws = MagicMock()
            mock_ws.exec_command.return_value = (0, "Cloning...", "")
            MockWS.return_value = mock_ws

            with patch.dict(os.environ, {"GIT_TOKEN": "ghp_secret123"}):
                from agent_on_call.orchestrator import OrchestratorAgent

                agent = OrchestratorAgent()
                ctx = MagicMock()
                result = await agent.git_clone(ctx, repo_url="https://github.com/user/repo.git")

                # Token should be in the command sent to exec
                call_cmd = mock_ws.exec_command.call_args[0][0]
                assert "ghp_secret123@github.com" in call_cmd
                # But NOT in the result returned to the LLM
                assert "ghp_secret123" not in result

    @pytest.mark.asyncio
    async def test_git_clone_with_branch(self):
        with patch("agent_on_call.orchestrator.WorkspaceManager") as MockWS:
            mock_ws = MagicMock()
            mock_ws.exec_command.return_value = (0, "Cloning...", "")
            MockWS.return_value = mock_ws

            from agent_on_call.orchestrator import OrchestratorAgent

            agent = OrchestratorAgent()
            ctx = MagicMock()
            await agent.git_clone(
                ctx,
                repo_url="https://github.com/user/repo.git",
                branch="develop",
            )

            call_cmd = mock_ws.exec_command.call_args[0][0]
            assert "-b develop" in call_cmd

    @pytest.mark.asyncio
    async def test_git_clone_with_path(self):
        with patch("agent_on_call.orchestrator.WorkspaceManager") as MockWS:
            mock_ws = MagicMock()
            mock_ws.exec_command.return_value = (0, "Cloning...", "")
            MockWS.return_value = mock_ws

            from agent_on_call.orchestrator import OrchestratorAgent

            agent = OrchestratorAgent()
            ctx = MagicMock()
            await agent.git_clone(
                ctx,
                repo_url="https://github.com/user/repo.git",
                path="/workspace/myrepo",
            )

            call_cmd = mock_ws.exec_command.call_args[0][0]
            assert "/workspace/myrepo" in call_cmd

    @pytest.mark.asyncio
    async def test_git_clone_empty_url(self):
        with patch("agent_on_call.orchestrator.WorkspaceManager"):
            from agent_on_call.orchestrator import OrchestratorAgent

            agent = OrchestratorAgent()
            ctx = MagicMock()
            result = await agent.git_clone(ctx, repo_url="")

            assert "error" in result.lower() or "empty" in result.lower()

    @pytest.mark.asyncio
    async def test_git_clone_auth_failure(self):
        with patch("agent_on_call.orchestrator.WorkspaceManager") as MockWS:
            mock_ws = MagicMock()
            mock_ws.exec_command.return_value = (
                128,
                "",
                "fatal: Authentication failed for 'https://github.com/user/private-repo.git'",
            )
            MockWS.return_value = mock_ws

            from agent_on_call.orchestrator import OrchestratorAgent

            agent = OrchestratorAgent()
            ctx = MagicMock()
            result = await agent.git_clone(ctx, repo_url="https://github.com/user/private-repo.git")

            assert "auth" in result.lower() or "failed" in result.lower()

    @pytest.mark.asyncio
    async def test_git_clone_uses_long_timeout(self):
        with patch("agent_on_call.orchestrator.WorkspaceManager") as MockWS:
            mock_ws = MagicMock()
            mock_ws.exec_command.return_value = (0, "Cloning...", "")
            MockWS.return_value = mock_ws

            from agent_on_call.orchestrator import OrchestratorAgent

            agent = OrchestratorAgent()
            ctx = MagicMock()
            await agent.git_clone(ctx, repo_url="https://github.com/user/repo.git")

            call_kwargs = mock_ws.exec_command.call_args
            assert call_kwargs[1].get("timeout", 30) >= 120


class TestGitStatusTool:
    @pytest.mark.asyncio
    async def test_git_status_success(self):
        with patch("agent_on_call.orchestrator.WorkspaceManager") as MockWS:
            mock_ws = MagicMock()
            mock_ws.exec_command.return_value = (
                0,
                "On branch main\nnothing to commit, working tree clean",
                "",
            )
            MockWS.return_value = mock_ws

            from agent_on_call.orchestrator import OrchestratorAgent

            agent = OrchestratorAgent()
            ctx = MagicMock()
            result = await agent.git_status(ctx)

            assert "On branch main" in result
            mock_ws.exec_command.assert_called_once()
            call_cmd = mock_ws.exec_command.call_args[0][0]
            assert "git status" in call_cmd

    @pytest.mark.asyncio
    async def test_git_status_no_workspace(self):
        with patch("agent_on_call.orchestrator.WorkspaceManager") as MockWS:
            mock_ws = MagicMock()
            mock_ws.exec_command.side_effect = RuntimeError("No active workspace. Create one first.")
            MockWS.return_value = mock_ws

            from agent_on_call.orchestrator import OrchestratorAgent

            agent = OrchestratorAgent()
            ctx = MagicMock()
            result = await agent.git_status(ctx)

            assert "No active workspace" in result


class TestGitCommitTool:
    @pytest.mark.asyncio
    async def test_git_commit_success(self):
        with patch("agent_on_call.orchestrator.WorkspaceManager") as MockWS:
            mock_ws = MagicMock()
            # First call: git add, second call: git commit
            mock_ws.exec_command.side_effect = [
                (0, "", ""),
                (0, "[main abc1234] Initial commit\n 1 file changed", ""),
            ]
            MockWS.return_value = mock_ws

            from agent_on_call.orchestrator import OrchestratorAgent

            agent = OrchestratorAgent()
            ctx = MagicMock()
            result = await agent.git_commit(ctx, message="Initial commit")

            assert "commit" in result.lower()
            calls = mock_ws.exec_command.call_args_list
            assert "git add" in calls[0][0][0]
            assert "git commit" in calls[1][0][0]
            assert "Initial commit" in calls[1][0][0]

    @pytest.mark.asyncio
    async def test_git_commit_specific_files(self):
        with patch("agent_on_call.orchestrator.WorkspaceManager") as MockWS:
            mock_ws = MagicMock()
            mock_ws.exec_command.side_effect = [
                (0, "", ""),
                (0, "[main abc1234] Update readme", ""),
            ]
            MockWS.return_value = mock_ws

            from agent_on_call.orchestrator import OrchestratorAgent

            agent = OrchestratorAgent()
            ctx = MagicMock()
            await agent.git_commit(ctx, message="Update readme", files="README.md src/main.py")

            calls = mock_ws.exec_command.call_args_list
            assert "README.md src/main.py" in calls[0][0][0]

    @pytest.mark.asyncio
    async def test_git_commit_nothing_to_commit(self):
        with patch("agent_on_call.orchestrator.WorkspaceManager") as MockWS:
            mock_ws = MagicMock()
            mock_ws.exec_command.side_effect = [
                (0, "", ""),
                (1, "nothing to commit, working tree clean", ""),
            ]
            MockWS.return_value = mock_ws

            from agent_on_call.orchestrator import OrchestratorAgent

            agent = OrchestratorAgent()
            ctx = MagicMock()
            result = await agent.git_commit(ctx, message="Empty commit")

            assert "nothing to commit" in result.lower()

    @pytest.mark.asyncio
    async def test_git_commit_empty_message(self):
        with patch("agent_on_call.orchestrator.WorkspaceManager"):
            from agent_on_call.orchestrator import OrchestratorAgent

            agent = OrchestratorAgent()
            ctx = MagicMock()
            result = await agent.git_commit(ctx, message="")

            assert "error" in result.lower() or "empty" in result.lower()


class TestGitPushTool:
    @pytest.mark.asyncio
    async def test_git_push_success(self):
        with patch("agent_on_call.orchestrator.WorkspaceManager") as MockWS:
            mock_ws = MagicMock()
            mock_ws.exec_command.return_value = (
                0,
                "",
                "To https://github.com/user/repo.git\n   abc1234..def5678  main -> main",
            )
            MockWS.return_value = mock_ws

            from agent_on_call.orchestrator import OrchestratorAgent

            agent = OrchestratorAgent()
            ctx = MagicMock()
            result = await agent.git_push(ctx)

            assert "push" in result.lower() or "main" in result.lower()
            call_cmd = mock_ws.exec_command.call_args[0][0]
            assert "git push" in call_cmd

    @pytest.mark.asyncio
    async def test_git_push_custom_remote_branch(self):
        with patch("agent_on_call.orchestrator.WorkspaceManager") as MockWS:
            mock_ws = MagicMock()
            mock_ws.exec_command.return_value = (0, "", "Everything up-to-date")
            MockWS.return_value = mock_ws

            from agent_on_call.orchestrator import OrchestratorAgent

            agent = OrchestratorAgent()
            ctx = MagicMock()
            await agent.git_push(ctx, remote="upstream", branch="develop")

            call_cmd = mock_ws.exec_command.call_args[0][0]
            assert "upstream" in call_cmd
            assert "develop" in call_cmd

    @pytest.mark.asyncio
    async def test_git_push_sanitizes_output(self):
        with patch("agent_on_call.orchestrator.WorkspaceManager") as MockWS:
            mock_ws = MagicMock()
            mock_ws.exec_command.return_value = (
                0,
                "",
                "To https://ghp_secret@github.com/user/repo.git\n   pushed",
            )
            MockWS.return_value = mock_ws

            with patch.dict(os.environ, {"GIT_TOKEN": "ghp_secret"}):
                from agent_on_call.orchestrator import OrchestratorAgent

                agent = OrchestratorAgent()
                ctx = MagicMock()
                result = await agent.git_push(ctx)

                assert "ghp_secret" not in result

    @pytest.mark.asyncio
    async def test_git_push_auth_failure(self):
        with patch("agent_on_call.orchestrator.WorkspaceManager") as MockWS:
            mock_ws = MagicMock()
            mock_ws.exec_command.return_value = (
                128,
                "",
                "fatal: Authentication failed",
            )
            MockWS.return_value = mock_ws

            from agent_on_call.orchestrator import OrchestratorAgent

            agent = OrchestratorAgent()
            ctx = MagicMock()
            result = await agent.git_push(ctx)

            assert "auth" in result.lower() or "failed" in result.lower()

    @pytest.mark.asyncio
    async def test_git_push_rejected(self):
        with patch("agent_on_call.orchestrator.WorkspaceManager") as MockWS:
            mock_ws = MagicMock()
            mock_ws.exec_command.return_value = (
                1,
                "",
                "! [rejected]        main -> main (non-fast-forward)",
            )
            MockWS.return_value = mock_ws

            from agent_on_call.orchestrator import OrchestratorAgent

            agent = OrchestratorAgent()
            ctx = MagicMock()
            result = await agent.git_push(ctx)

            assert "rejected" in result.lower() or "failed" in result.lower()


class TestWebSearchTool:
    def test_orchestrator_has_web_search_tool(self):
        with patch("agent_on_call.orchestrator.WorkspaceManager"):
            from agent_on_call.orchestrator import OrchestratorAgent

            agent = OrchestratorAgent()
            assert hasattr(agent, "web_search")

    def test_orchestrator_has_web_fetch_tool(self):
        with patch("agent_on_call.orchestrator.WorkspaceManager"):
            from agent_on_call.orchestrator import OrchestratorAgent

            agent = OrchestratorAgent()
            assert hasattr(agent, "web_fetch")

    def test_orchestrator_has_web_tool_instance(self):
        with patch("agent_on_call.orchestrator.WorkspaceManager"):
            from agent_on_call.orchestrator import OrchestratorAgent

            agent = OrchestratorAgent()
            assert hasattr(agent, "_web")

    @pytest.mark.asyncio
    async def test_web_search_delegates_to_web_tool(self):
        with patch("agent_on_call.orchestrator.WorkspaceManager"):
            from agent_on_call.orchestrator import OrchestratorAgent

            agent = OrchestratorAgent()
            agent._web.search = AsyncMock(return_value="1. **Result**\n   URL: https://example.com\n   Snippet")
            ctx = MagicMock()
            result = await agent.web_search(ctx, query="test query")
            agent._web.search.assert_awaited_once_with("test query")
            assert "Result" in result

    @pytest.mark.asyncio
    async def test_web_fetch_delegates_to_web_tool(self):
        with patch("agent_on_call.orchestrator.WorkspaceManager"):
            from agent_on_call.orchestrator import OrchestratorAgent

            agent = OrchestratorAgent()
            agent._web.fetch = AsyncMock(return_value="Page content here")
            ctx = MagicMock()
            result = await agent.web_fetch(ctx, url="https://example.com")
            agent._web.fetch.assert_awaited_once_with("https://example.com")
            assert "Page content" in result
