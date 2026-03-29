"""Orchestrator Agent — voice interface and sub-agent coordination."""

import json
import logging
import os
import time

from livekit.agents import Agent, RunContext
from livekit.agents.llm import function_tool

logger = logging.getLogger(__name__)

from agent_on_call.code_analysis import CodeAnalysisTool
from agent_on_call.guidance_queue import GuidanceQueue
from agent_on_call.web_tools import WebSearchTool
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
        self._web = WebSearchTool()
        self._code = CodeAnalysisTool(self._workspace)
        self._room = None

    def set_room(self, room) -> None:
        """Set the room reference for publishing action events via data channel."""
        self._room = room

    async def _emit_action(
        self,
        kind: str,
        tool: str,
        summary: str,
        detail: str = "",
        status: str = "started",
        action_id: str | None = None,
    ) -> str:
        """Publish an agent action event to the frontend via data channel.

        Args:
            kind: Action type — "thinking", "executing", "tool_call", or "result"
            tool: The function_tool name (e.g., "exec_command", "git_clone")
            summary: Human-readable one-liner for the activity panel
            detail: Full command or output (shown when expanded)
            status: Lifecycle state — "started", "completed", or "failed"
            action_id: Optional action ID (auto-generated if None)

        Returns:
            The action ID used for this event.
        """
        if action_id is None:
            action_id = f"action-{int(time.time() * 1000)}-{tool}"

        if self._room is None:
            return action_id
        message = json.dumps(
            {
                "type": "agent_action",
                "action": {
                    "id": action_id,
                    "kind": kind,
                    "tool": tool,
                    "summary": summary,
                    "detail": detail,
                    "status": status,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                },
            }
        )
        try:
            await self._room.local_participant.publish_data(
                message.encode(),
                topic="agent_actions",
            )
        except Exception as e:
            logger.warning("Failed to emit action event: %s", e)
        return action_id

    async def _emit_command_output(
        self,
        command_id: str,
        command: str,
        output: str,
        exit_code: int,
        done: bool = True,
    ) -> None:
        """Publish command output to the frontend via data channel.

        This sends the full command output (not truncated) so the terminal
        panel can display it. Chunks are capped at 100KB to prevent
        excessive data channel usage.

        Args:
            command_id: Unique ID matching the action event
            command: The command that was executed
            output: The output text (stdout + stderr)
            exit_code: The command exit code
            done: Whether the command has finished
        """
        if self._room is None:
            return

        # Cap output at 100KB
        max_output = 100 * 1024
        if len(output) > max_output:
            output = output[:max_output] + "\n...(output truncated at 100KB)..."

        message = json.dumps(
            {
                "type": "command_output",
                "id": command_id,
                "command": command,
                "output": output,
                "exitCode": exit_code,
                "done": done,
            }
        )
        try:
            await self._room.local_participant.publish_data(
                message.encode(),
                topic="command_output",
            )
        except Exception as e:
            logger.warning("Failed to emit command output: %s", e)

    @function_tool
    async def create_workspace(self, context: RunContext, name: str, clean: bool = True) -> str:
        """Create a new isolated workspace for a project. Use a short descriptive name like 'my-app' or 'data-analysis'.

        Args:
            name: Short descriptive name for the workspace.
            clean: If True (default), removes any existing workspace with the same name first.
                   Set to False to resume a previous workspace.
        """
        action = "Creating" if clean else "Resuming"
        await self._emit_action("tool_call", "create_workspace", f"{action} workspace '{name}'...")
        try:
            container_id = self._workspace.create_workspace(name, clean=clean)
            await self._emit_action("result", "create_workspace", f"Workspace '{name}' {'created' if clean else 'resumed'}", status="completed")
            return f"Workspace '{name}' {'created' if clean else 'resumed'} successfully (container: {container_id[:12]})"
        except Exception as e:
            await self._emit_action("result", "create_workspace", f"Failed to create workspace: {e}", status="failed")
            return f"Failed to create workspace: {e}"

    @function_tool
    async def exec_command(self, context: RunContext, command: str, timeout: int = 30) -> str:
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
        cmd_action_id = await self._emit_action(
            "executing",
            "exec_command",
            f"Running: {command[:80]}{'...' if len(command) > 80 else ''}",
            detail=command,
        )
        try:
            exit_code, stdout, stderr = self._workspace.exec_command(command, timeout=timeout)

            # Publish full output to terminal panel via command_output channel
            full_output = ""
            if stdout:
                full_output += stdout
            if stderr:
                if full_output:
                    full_output += "\n"
                full_output += stderr
            await self._emit_command_output(
                command_id=cmd_action_id,
                command=command,
                output=full_output,
                exit_code=exit_code,
                done=True,
            )

            # Truncate for LLM context (the full output was already sent to terminal)
            if len(stdout) > 2000:
                stdout = stdout[:1000] + "\n...(truncated)...\n" + stdout[-500:]
            if len(stderr) > 1000:
                stderr = stderr[:500] + "\n...(truncated)...\n" + stderr[-200:]
            result = f"Exit code: {exit_code}\n\n" f"Stdout:\n{stdout}\n\n" f"Stderr:\n{stderr}"
            status = "completed" if exit_code == 0 else "failed"
            await self._emit_action(
                "result",
                "exec_command",
                f"Command {'completed' if exit_code == 0 else 'failed'} (exit {exit_code})",
                detail=stdout[:200] if stdout else stderr[:200],
                status=status,
                action_id=cmd_action_id,
            )
            return result
        except TimeoutError:
            await self._emit_command_output(
                command_id=cmd_action_id,
                command=command,
                output=f"Command timed out after {timeout}s",
                exit_code=-1,
                done=True,
            )
            await self._emit_action(
                "result", "exec_command",
                f"Command timed out after {timeout}s",
                status="failed",
                action_id=cmd_action_id,
            )
            return f"Error: Command timed out after {timeout}s: {command[:100]}"
        except RuntimeError as e:
            await self._emit_command_output(
                command_id=cmd_action_id,
                command=command,
                output=str(e),
                exit_code=-1,
                done=True,
            )
            await self._emit_action(
                "result", "exec_command",
                f"Error: {e}",
                status="failed",
                action_id=cmd_action_id,
            )
            return f"Error: {e}"

    @function_tool
    async def read_file(self, context: RunContext, path: str) -> str:
        """Read the contents of a file in the workspace."""
        await self._emit_action("tool_call", "read_file", f"Reading: {path}")
        try:
            content = self._workspace.read_file(path)
            if len(content) > 3000:
                content = content[:1500] + "\n...(truncated)...\n" + content[-500:]
            await self._emit_action("result", "read_file", f"Read {len(content)} chars from {path}", status="completed")
            return content
        except FileNotFoundError as e:
            await self._emit_action("result", "read_file", f"File not found: {path}", status="failed")
            return f"Error: {e}"

    @function_tool
    async def write_file(self, context: RunContext, path: str, content: str) -> str:
        """Write content to a file in the workspace."""
        await self._emit_action("tool_call", "write_file", f"Writing: {path}")
        try:
            result = self._workspace.write_file(path, content)
            await self._emit_action("result", "write_file", f"Written to {path}", status="completed")
            return result
        except IOError as e:
            await self._emit_action("result", "write_file", f"Write failed: {path}", status="failed")
            return f"Error: {e}"

    @function_tool
    async def list_files(self, context: RunContext, path: str = "/workspace") -> str:
        """List files and directories in the workspace."""
        await self._emit_action("tool_call", "list_files", f"Listing: {path}")
        result = self._workspace.list_files(path)
        await self._emit_action("result", "list_files", f"Listed files in {path}", status="completed")
        return result

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

        clone_action_id = await self._emit_action("executing", "git_clone", f"Cloning: {repo_url}")
        token = self._get_git_token()
        credentialed_url = inject_git_credentials(repo_url, token)

        cmd_parts = ["git clone"]
        if branch:
            cmd_parts.append(f"-b {branch}")
        cmd_parts.append(credentialed_url)
        if path:
            cmd_parts.append(path)

        cmd = " ".join(cmd_parts)
        # Display URL (sanitized) for terminal panel
        display_cmd = sanitize_git_output(cmd, token)

        try:
            exit_code, stdout, stderr = self._workspace.exec_command(cmd, timeout=120)
            # Sanitize output to remove credentials
            stdout = sanitize_git_output(stdout, token)
            stderr = sanitize_git_output(stderr, token)

            output = stdout or stderr or ""
            await self._emit_command_output(
                command_id=clone_action_id,
                command=display_cmd,
                output=output,
                exit_code=exit_code,
                done=True,
            )

            if exit_code != 0:
                error_msg = stderr or stdout
                if "authentication failed" in error_msg.lower():
                    return "Error: Authentication failed. " "Check GIT_TOKEN environment variable for private repos."
                return f"Clone failed (exit {exit_code}):\n{error_msg}"

            result = stdout or stderr or "Clone completed successfully."
            await self._emit_action("result", "git_clone", "Clone completed", status="completed", action_id=clone_action_id)
            return sanitize_git_output(result, token)
        except TimeoutError:
            await self._emit_command_output(
                command_id=clone_action_id, command=display_cmd,
                output="Clone timed out after 120s", exit_code=-1, done=True,
            )
            await self._emit_action("result", "git_clone", "Clone timed out", status="failed", action_id=clone_action_id)
            return "Error: Clone timed out after 120s. The repository may be very large."
        except RuntimeError as e:
            await self._emit_command_output(
                command_id=clone_action_id, command=display_cmd,
                output=str(e), exit_code=-1, done=True,
            )
            await self._emit_action("result", "git_clone", f"Error: {e}", status="failed", action_id=clone_action_id)
            return f"Error: {e}"

    @function_tool
    async def git_status(self, context: RunContext) -> str:
        """Show the git working tree status in the workspace."""
        await self._emit_action("tool_call", "git_status", "Checking git status")
        try:
            exit_code, stdout, stderr = self._workspace.exec_command("git status")
            if exit_code != 0:
                await self._emit_action("result", "git_status", "git status failed", status="failed")
                return f"git status failed:\n{stderr or stdout}"
            await self._emit_action("result", "git_status", "Status retrieved", status="completed")
            return stdout
        except RuntimeError as e:
            await self._emit_action("result", "git_status", f"Error: {e}", status="failed")
            return f"Error: {e}"

    @function_tool
    async def git_commit(self, context: RunContext, message: str, files: str = ".") -> str:
        """Stage files and commit with a message.

        Args:
            message: The commit message.
            files: Space-separated file paths to stage (default: '.' for all changes).
        """
        if not message or not message.strip():
            return "Error: Commit message cannot be empty."

        await self._emit_action("executing", "git_commit", f"Committing: {message[:60]}")
        try:
            # Stage files
            exit_code, stdout, stderr = self._workspace.exec_command(f"git add {files}")
            if exit_code != 0:
                await self._emit_action("result", "git_commit", "git add failed", status="failed")
                return f"git add failed:\n{stderr or stdout}"

            # Commit
            # Escape single quotes in message
            safe_message = message.replace("'", "'\\''")
            exit_code, stdout, stderr = self._workspace.exec_command(f"git commit -m '{safe_message}'")
            if exit_code != 0:
                output = stdout or stderr
                if "nothing to commit" in output.lower():
                    await self._emit_action("result", "git_commit", "Nothing to commit", status="completed")
                    return "Nothing to commit — working tree is clean."
                await self._emit_action("result", "git_commit", "Commit failed", status="failed")
                return f"git commit failed:\n{output}"

            await self._emit_action("result", "git_commit", "Committed successfully", status="completed")
            return f"Committed successfully:\n{stdout}"
        except RuntimeError as e:
            await self._emit_action("result", "git_commit", f"Error: {e}", status="failed")
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

        await self._emit_action("executing", "git_push", f"Pushing to {remote}" + (f" {branch}" if branch else ""))
        try:
            exit_code, stdout, stderr = self._workspace.exec_command(cmd)
            stdout = sanitize_git_output(stdout, token)
            stderr = sanitize_git_output(stderr, token)

            if exit_code != 0:
                error_msg = stderr or stdout
                if "authentication failed" in error_msg.lower():
                    await self._emit_action("result", "git_push", "Authentication failed", status="failed")
                    return "Error: Authentication failed. " "Check GIT_TOKEN environment variable."
                if "rejected" in error_msg.lower():
                    await self._emit_action("result", "git_push", "Push rejected", status="failed")
                    return (
                        f"Push rejected:\n{error_msg}\n\n"
                        "The remote has changes you don't have locally. "
                        "Try pulling first."
                    )
                await self._emit_action("result", "git_push", f"Push failed (exit {exit_code})", status="failed")
                return f"Push failed (exit {exit_code}):\n{error_msg}"

            result = stderr or stdout or "Push completed successfully."
            await self._emit_action("result", "git_push", "Push completed", status="completed")
            return sanitize_git_output(result, token)
        except RuntimeError as e:
            await self._emit_action("result", "git_push", f"Error: {e}", status="failed")
            return f"Error: {e}"

    @function_tool
    async def web_search(self, context: RunContext, query: str) -> str:
        """Search the web for information. Returns top results with titles, URLs, and snippets.

        Use this to find documentation, Stack Overflow answers, API references, or any web resource.

        Args:
            query: The search query string.
        """
        await self._emit_action("tool_call", "web_search", f"Searching: {query[:80]}")
        result = await self._web.search(query)
        status = "failed" if result.startswith("Error") else "completed"
        await self._emit_action(
            "result", "web_search", f"Search {'completed' if status == 'completed' else 'failed'}", status=status
        )
        return result

    @function_tool
    async def web_fetch(self, context: RunContext, url: str) -> str:
        """Fetch a web page and return its text content. HTML is converted to plain text.

        Use this after web_search to read a specific page in detail.

        Args:
            url: The full URL to fetch (must start with http:// or https://).
        """
        await self._emit_action("tool_call", "web_fetch", f"Fetching: {url[:80]}")
        result = await self._web.fetch(url)
        status = "failed" if result.startswith("Error") else "completed"
        await self._emit_action(
            "result", "web_fetch", f"Fetch {'completed' if status == 'completed' else 'failed'}", status=status
        )
        return result

    @function_tool
    async def analyze_codebase(
        self,
        context: RunContext,
        path: str = "/workspace",
        query: str = "",
        depth: int = 3,
    ) -> str:
        """Analyze a codebase directory — returns project structure, file stats, and stack detection.

        Use this to understand a project's layout before diving into specific files.
        Optionally search for a pattern across source files.

        Args:
            path: Directory to analyze (default: /workspace).
            query: Optional search pattern to grep for in source files.
            depth: Tree depth limit (default: 3). Increase for deeper exploration.
        """
        summary = f"Analyzing: {path}" + (f" (searching for '{query}')" if query else "")
        await self._emit_action("tool_call", "analyze_codebase", summary)
        result = await self._code.analyze(path=path, query=query, depth=depth)
        status = "failed" if result.startswith("Error") else "completed"
        await self._emit_action("result", "analyze_codebase", f"Analysis {status}", status=status)
        return result
