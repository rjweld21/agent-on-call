# Shell Command Execution Tool — Implementation Plan

**Date:** 2026-03-25
**Story:** #1 — Add shell command execution tool
**Spec:** `docs/superpowers/specs/2026-03-25-shell-command-tool-design.md`

## Tasks

### Task 1: Update WorkspaceManager.exec_command to separate stdout/stderr and add timeout

**Files:** `src/agent_on_call/workspace.py`, `tests/test_workspace.py`

1. Write tests first:
   - Test exec_command returns (exit_code, stdout, stderr) as 3-tuple
   - Test timeout parameter raises TimeoutError after N seconds
   - Test command on stopped container restarts it (existing behavior, update assertions)
   - Test empty stdout/stderr returns empty strings
2. Update `exec_command` signature:
   ```python
   def exec_command(self, command: str, workdir: str = "/workspace", timeout: int = 30) -> tuple[int, str, str]:
   ```
3. Split `result.output` into separate stdout and stderr
4. Add timeout support using `concurrent.futures.ThreadPoolExecutor` + `asyncio` (or plain threading for sync method)
5. Raise `TimeoutError` with descriptive message on timeout
6. Update internal callers (`read_file`, `write_file`, `list_files`) to handle 3-tuple

### Task 2: Add exec_command function tool to OrchestratorAgent

**Files:** `src/agent_on_call/orchestrator.py`, `tests/test_orchestrator.py`

1. Write tests first:
   - Test exec_command tool exists on OrchestratorAgent
   - Test successful command returns structured output with exit code, stdout, stderr
   - Test failed command (non-zero exit) returns structured output
   - Test timeout returns clear timeout error message
   - Test command length validation rejects >10000 chars
   - Test empty command returns error
2. Add `exec_command` method with `@function_tool` decorator
3. Validate command (not empty, within length limit)
4. Delegate to `self._workspace.exec_command(command, timeout=timeout)`
5. Format output as structured string
6. Handle `TimeoutError` and `RuntimeError` with clear messages
7. Remove or rename the existing `run_command` tool to avoid duplication

### Task 3: Update existing tool methods for 3-tuple return

**Files:** `src/agent_on_call/orchestrator.py`, `tests/test_orchestrator.py`

1. Update `run_command` (or remove if replaced by exec_command)
2. Update `read_file` tool to use stdout from 3-tuple
3. Update `write_file` tool to use stderr from 3-tuple for error messages
4. Update `list_files` tool to use stdout from 3-tuple
5. Update existing tests for the new return signature

### Task 4: Verify all acceptance criteria

1. Run full test suite: `pytest --cov -v`
2. Verify coverage >= 90% on new code
3. Check each AC manually against implementation

## Dependencies

- WorkspaceManager must support Docker SDK exec operations (already exists)
- No external dependencies need to be added

## Risk

- Timeout implementation: the exec process may linger in the container after timeout. Acceptable for MVP.
- Changing exec_command return type is a breaking change for internal callers. Mitigated by updating all callers in the same PR.
