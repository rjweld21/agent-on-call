"""Orchestrator Agent — stub for Task 6, full implementation in Task 7."""

from livekit.agents import Agent


class OrchestratorAgent(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="You are the Agent On Call orchestrator.")
