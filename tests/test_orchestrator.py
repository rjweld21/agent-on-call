"""Tests for OrchestratorAgent."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


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
            mock_ws.exec_command.assert_called_once_with(
                "echo hello world", timeout=30
            )

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
            mock_ws.exec_command.side_effect = TimeoutError(
                "Command timed out after 5s"
            )
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
            mock_ws.exec_command.side_effect = RuntimeError(
                "No active workspace. Create one first."
            )
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

            mock_ws.exec_command.assert_called_once_with(
                "pip install", timeout=120
            )

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
