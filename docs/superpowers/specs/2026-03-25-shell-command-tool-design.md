# Shell Command Execution Tool — Design Spec

**Date:** 2026-03-25
**Story:** #1 — Add shell command execution tool

## Overview

Add an `exec_command` function tool to the OrchestratorAgent that exposes shell command execution to the LLM. The tool delegates to the existing `WorkspaceManager.exec_command()` method, adding timeout enforcement, command validation, and structured output formatting.

## Design Decisions

### Tool Signature

```python
@function_tool
async def exec_command(self, context: RunContext, command: str, timeout: int = 30) -> str:
```

- **Single tool for all commands** — keeps the LLM tool list small and flexible
- **Timeout parameter** — allows the LLM to increase timeout for long-running commands (e.g., `pip install`)
- **Default 30s** — safe default that handles most quick commands

### Why Modify the Existing `run_command` Tool

The existing `run_command` tool on OrchestratorAgent already delegates to `WorkspaceManager.exec_command()`. However, it lacks:
1. Configurable timeout (the workspace `exec_command` has no timeout)
2. Structured output format (exit code + stdout + stderr separated)
3. Command length validation
4. Clean kill on timeout exceed

The story asks for `exec_command` as a distinct `function_tool`. Since `run_command` already exists and does nearly the same thing, the implementation will **replace** `run_command` with `exec_command` (keeping the same behavior but adding the new features). This avoids having two nearly-identical tools exposed to the LLM.

### Timeout Implementation

The Docker SDK's `exec_run` does not natively support timeouts. Implementation approach:
1. Use `exec_create` + `exec_start` (lower-level API) with a socket connection
2. Wrap in `asyncio.wait_for` with the specified timeout
3. On timeout: use Docker API to kill the exec process (not the container)
4. Return a clear timeout error message

Alternative (simpler): Use `exec_run` in a thread pool executor with `asyncio.wait_for`. If timeout triggers, the exec may continue running in the container, but the tool returns immediately with a timeout error. The container stays alive for subsequent commands.

**Decision:** Use the simpler thread pool approach for MVP. The exec process may linger but the container remains usable. Add process cleanup in a future enhancement if needed.

### Command Validation

- **Max command length:** 10,000 characters (prevents accidental paste of large content)
- **No empty commands:** Return error for empty/whitespace-only input

### Output Format

Structured output returned to the LLM:
```
Exit code: {code}

Stdout:
{stdout}

Stderr:
{stderr}
```

This format gives the LLM all three pieces of information to reason about. The existing `run_command` mixes stdout+stderr, which makes it harder for the LLM to distinguish warnings from output.

### WorkspaceManager Changes

Add a `timeout` parameter to `WorkspaceManager.exec_command()`:
```python
def exec_command(self, command: str, workdir: str = "/workspace", timeout: int = 30) -> tuple[int, str, str]:
```

Changes:
- Return `(exit_code, stdout, stderr)` instead of `(exit_code, combined_output)` — separating stdout and stderr
- Add timeout support via threading
- Raise `TimeoutError` on timeout exceed

### Backward Compatibility

The existing `run_command` tool concatenates stdout and stderr. Changing the return type of `WorkspaceManager.exec_command()` will require updating `run_command`. Since we're replacing `run_command` with `exec_command`, this is handled by the replacement.

Other callers of `WorkspaceManager.exec_command()`:
- `read_file` — uses exit_code and combined output. Update to use stdout only.
- `write_file` — uses exit_code and combined output. Update to use stderr for error messages.
- `list_files` — uses exit_code and combined output. Update to use stdout only.

## File Structure

```
src/agent_on_call/workspace.py        — Update exec_command signature and add timeout
src/agent_on_call/orchestrator.py      — Replace run_command with exec_command
tests/test_workspace.py                — Add timeout tests, update existing tests
tests/test_orchestrator.py             — Add exec_command tool tests
```

## Out of Scope

- Interactive/TTY commands (vim, top)
- Real-time output streaming
- Command allowlisting/blocklisting
- Process cleanup on timeout (exec may linger)
