"""Orchestrator Agent — voice interface and sub-agent coordination."""

from livekit.agents import Agent, RunContext
from livekit.agents.llm import function_tool

from agent_on_call.guidance_queue import GuidanceQueue
from agent_on_call.workspace import WorkspaceManager

ORCHESTRATOR_INSTRUCTIONS = """You are the Agent On Call orchestrator — a helpful AI assistant \
on a voice call with the user. Your display name is "Orchestrator".

You have access to workspace tools that let you execute commands, read/write files, and manage \
projects in isolated environments.

IMPORTANT — Environment awareness:
- Your workspace is an isolated environment, separate from the user's computer.
- You and the user are on two separate machines. Files you create are NOT on the user's computer.
- If you spin up a web server or app, it is NOT accessible to the user unless they set up port forwarding.
- When you run commands, the output is only visible to you unless you share it verbally or it appears in the UI.
- Do NOT refer to Docker, containers, or infrastructure details — just say "my workspace" or "my environment".

When the user asks you to work on a project:
1. Create a workspace if one doesn't exist: use create_workspace with a short name
2. Clone repos, install dependencies, run commands using run_command
3. Read and write files as needed

When a user pastes a URL or code in the text chat, use your tools to act on it.

Keep your responses conversational and concise — this is a voice call, not a text chat. \
When sharing command output, summarize the key points rather than reading every line. \
For detailed output, tell the user they can see it in the terminal panel."""


class OrchestratorAgent(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=ORCHESTRATOR_INSTRUCTIONS)
        self.guidance_queue = GuidanceQueue()
        self._workspace = WorkspaceManager()

    @function_tool
    async def create_workspace(self, context: RunContext, name: str) -> str:
        """Create a new isolated workspace for a project. Use a short descriptive name like 'my-app' or 'data-analysis'."""
        try:
            container_id = self._workspace.create_workspace(name)
            return f"Workspace '{name}' created successfully (container: {container_id[:12]})"
        except Exception as e:
            return f"Failed to create workspace: {e}"

    @function_tool
    async def run_command(self, context: RunContext, command: str) -> str:
        """Run a shell command in the active workspace. Use for: git clone, pip install, pytest, ls, etc."""
        try:
            exit_code, output = self._workspace.exec_command(command)
            # Truncate very long output
            if len(output) > 2000:
                output = output[:1000] + "\n...(truncated)...\n" + output[-500:]
            status = "success" if exit_code == 0 else f"failed (exit code {exit_code})"
            return f"[{status}]\n{output}"
        except RuntimeError as e:
            return f"Error: {e}"

    @function_tool
    async def read_file(self, context: RunContext, path: str) -> str:
        """Read the contents of a file in the workspace."""
        try:
            content = self._workspace.read_file(path)
            if len(content) > 3000:
                content = content[:1500] + "\n...(truncated)...\n" + content[-500:]
            return content
        except FileNotFoundError as e:
            return f"Error: {e}"

    @function_tool
    async def write_file(self, context: RunContext, path: str, content: str) -> str:
        """Write content to a file in the workspace."""
        try:
            return self._workspace.write_file(path, content)
        except IOError as e:
            return f"Error: {e}"

    @function_tool
    async def list_files(self, context: RunContext, path: str = "/workspace") -> str:
        """List files and directories in the workspace."""
        return self._workspace.list_files(path)

    @function_tool
    async def list_workspaces(self, context: RunContext) -> str:
        """List all available workspaces and their status."""
        workspaces = self._workspace.list_workspaces()
        if not workspaces:
            return "No workspaces found. Create one with create_workspace."
        lines = [f"- {w['name']} ({w['status']})" for w in workspaces]
        active = self._workspace.get_active_workspace()
        if active:
            lines.append(f"\nActive workspace: {active}")
        return "\n".join(lines)
