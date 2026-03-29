"""Orchestrator Agent — voice interface and sub-agent coordination."""

import os

from livekit.agents import Agent, RunContext
from livekit.agents.llm import function_tool

from agent_on_call.guidance_queue import GuidanceQueue
from agent_on_call.workspace import (
    WorkspaceManager,
    inject_git_credentials,
    sanitize_git_output,
)

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
    async def exec_command(
        self, context: RunContext, command: str, timeout: int = 30
    ) -> str:
        """Execute a shell command in the active workspace. Use for: git, pip, pytest, ls, etc.

        Args:
            command: The shell command to run.
            timeout: Max seconds to wait (default 30). Increase for long-running commands.
        """
        if not command or not command.strip():
            return "Error: Command cannot be empty."
        if len(command) > 10000:
            return (
                "Error: Command too long "
                f"({len(command)} chars, max 10000). "
                "Consider writing to a script file and executing it."
            )
        try:
            exit_code, stdout, stderr = self._workspace.exec_command(
                command, timeout=timeout
            )
            # Truncate very long output
            if len(stdout) > 2000:
                stdout = stdout[:1000] + "\n...(truncated)...\n" + stdout[-500:]
            if len(stderr) > 1000:
                stderr = stderr[:500] + "\n...(truncated)...\n" + stderr[-200:]
            return (
                f"Exit code: {exit_code}\n\n"
                f"Stdout:\n{stdout}\n\n"
                f"Stderr:\n{stderr}"
            )
        except TimeoutError:
            return f"Error: Command timed out after {timeout}s: {command[:100]}"
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

    def _get_git_token(self) -> str | None:
        """Get the git token from environment variables."""
        return os.environ.get("GIT_TOKEN")

    @function_tool
    async def git_clone(
        self,
        context: RunContext,
        repo_url: str,
        branch: str = "",
        path: str = "",
    ) -> str:
        """Clone a git repository into the workspace.

        Args:
            repo_url: The repository URL (HTTPS or SSH).
            branch: Optional branch to clone (default: repo default branch).
            path: Optional target directory path (default: auto from repo name).
        """
        if not repo_url or not repo_url.strip():
            return "Error: Repository URL cannot be empty."

        token = self._get_git_token()
        credentialed_url = inject_git_credentials(repo_url, token)

        cmd_parts = ["git clone"]
        if branch:
            cmd_parts.append(f"-b {branch}")
        cmd_parts.append(credentialed_url)
        if path:
            cmd_parts.append(path)

        cmd = " ".join(cmd_parts)

        try:
            exit_code, stdout, stderr = self._workspace.exec_command(
                cmd, timeout=120
            )
            # Sanitize output to remove credentials
            stdout = sanitize_git_output(stdout, token)
            stderr = sanitize_git_output(stderr, token)

            if exit_code != 0:
                error_msg = stderr or stdout
                if "authentication failed" in error_msg.lower():
                    return (
                        "Error: Authentication failed. "
                        "Check GIT_TOKEN environment variable for private repos."
                    )
                return f"Clone failed (exit {exit_code}):\n{error_msg}"

            result = stdout or stderr or "Clone completed successfully."
            return sanitize_git_output(result, token)
        except TimeoutError:
            return "Error: Clone timed out after 120s. The repository may be very large."
        except RuntimeError as e:
            return f"Error: {e}"

    @function_tool
    async def git_status(self, context: RunContext) -> str:
        """Show the git working tree status in the workspace."""
        try:
            exit_code, stdout, stderr = self._workspace.exec_command(
                "git status"
            )
            if exit_code != 0:
                return f"git status failed:\n{stderr or stdout}"
            return stdout
        except RuntimeError as e:
            return f"Error: {e}"

    @function_tool
    async def git_commit(
        self, context: RunContext, message: str, files: str = "."
    ) -> str:
        """Stage files and commit with a message.

        Args:
            message: The commit message.
            files: Space-separated file paths to stage (default: '.' for all changes).
        """
        if not message or not message.strip():
            return "Error: Commit message cannot be empty."

        try:
            # Stage files
            exit_code, stdout, stderr = self._workspace.exec_command(
                f"git add {files}"
            )
            if exit_code != 0:
                return f"git add failed:\n{stderr or stdout}"

            # Commit
            # Escape single quotes in message
            safe_message = message.replace("'", "'\\''")
            exit_code, stdout, stderr = self._workspace.exec_command(
                f"git commit -m '{safe_message}'"
            )
            if exit_code != 0:
                output = stdout or stderr
                if "nothing to commit" in output.lower():
                    return "Nothing to commit — working tree is clean."
                return f"git commit failed:\n{output}"

            return f"Committed successfully:\n{stdout}"
        except RuntimeError as e:
            return f"Error: {e}"

    @function_tool
    async def git_push(
        self,
        context: RunContext,
        remote: str = "origin",
        branch: str = "",
    ) -> str:
        """Push commits to a remote repository.

        Args:
            remote: The remote name (default: 'origin').
            branch: The branch to push (default: current branch).
        """
        token = self._get_git_token()

        cmd = f"git push {remote}"
        if branch:
            cmd += f" {branch}"

        try:
            exit_code, stdout, stderr = self._workspace.exec_command(cmd)
            stdout = sanitize_git_output(stdout, token)
            stderr = sanitize_git_output(stderr, token)

            if exit_code != 0:
                error_msg = stderr or stdout
                if "authentication failed" in error_msg.lower():
                    return (
                        "Error: Authentication failed. "
                        "Check GIT_TOKEN environment variable."
                    )
                if "rejected" in error_msg.lower():
                    return (
                        f"Push rejected:\n{error_msg}\n\n"
                        "The remote has changes you don't have locally. "
                        "Try pulling first."
                    )
                return f"Push failed (exit {exit_code}):\n{error_msg}"

            result = stderr or stdout or "Push completed successfully."
            return sanitize_git_output(result, token)
        except RuntimeError as e:
            return f"Error: {e}"
