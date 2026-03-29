# Clean Workspace Implementation Plan — Story #59

## Branch: `feat/clean-workspace`
## Base: `master`

## Tasks

### Task 1: Add cleanup logic to `WorkspaceManager.create_workspace`
**File:** `src/agent_on_call/workspace.py`
**Changes:**
- Add `clean: bool = True` parameter to `create_workspace`
- When `clean=True`: call `delete_workspace(name)` before creating (already handles NotFound)
- When `clean=False`:
  - Try to get existing container `aoc-ws-{name}`
  - If running: set as active and return its ID
  - If stopped: start it, set as active, return its ID
  - If not found: create fresh

### Task 2: Update `OrchestratorAgent.create_workspace` tool
**File:** `src/agent_on_call/orchestrator.py`
**Changes:**
- Add `clean: bool = True` parameter to the function_tool
- Pass through to `self._workspace.create_workspace(name, clean=clean)`
- Update docstring

### Task 3: Write unit tests for workspace cleanup
**File:** `tests/test_workspace.py`
**Changes:**
- Test `create_workspace` with `clean=True` calls `delete_workspace` then creates fresh
- Test `create_workspace` with `clean=False` reuses running container
- Test `create_workspace` with `clean=False` starts stopped container
- Test `create_workspace` with `clean=False` creates fresh when no container exists
- Test default behavior is `clean=True`

### Task 4: Write unit test for orchestrator tool parameter
**File:** `tests/test_orchestrator.py`
**Changes:**
- Test that `create_workspace` tool passes `clean` parameter to workspace manager

## Test-First Order
1. Write tests for tasks 3-4 (they should fail)
2. Implement task 1
3. Run workspace tests (should pass)
4. Implement task 2
5. Run orchestrator tests (should pass)

## Dependencies
- None — independent of #57/#58
