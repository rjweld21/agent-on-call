"""Tests for OrchestratorAgent."""

from unittest.mock import patch


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
