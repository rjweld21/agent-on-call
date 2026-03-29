# Rich Activity Events Implementation Plan — Story #58

## Branch: `feat/rich-activity-events`
## Base: `master`

## Tasks

### Task 1: Add activity events to `list_workspaces`
**File:** `src/agent_on_call/orchestrator.py`
- Add `_emit_action` start event with "Listing workspaces..."
- Add `_emit_action` completion event with count

### Task 2: Thread action_id through `read_file`, `write_file`, `list_files`
**File:** `src/agent_on_call/orchestrator.py`
- Capture action_id from start `_emit_action` call
- Pass `action_id=...` to completion/failure `_emit_action` call

### Task 3: Improve summary text for all tools
**File:** `src/agent_on_call/orchestrator.py`
- Update summary strings to match spec format (more descriptive, consistent prefix)

### Task 4: Write tests
**File:** `tests/test_orchestrator.py`
- Test list_workspaces emits events
- Test action_id threading for file tools
- Test summary text format

## Test-First Order
1. Write tests (should fail for list_workspaces events and action_id threading)
2. Implement changes
3. Verify all tests pass
