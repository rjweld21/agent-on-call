# Terminal Wiring Implementation Plan — Story #57

## Branch: `feat/terminal-wiring`
## Base: `master`

## Tasks

### Task 1: Add `_emit_command_output` to `git_status`
**File:** `src/agent_on_call/orchestrator.py`
**Changes:**
- Generate action ID from `_emit_action` return value (already done — `_emit_action` returns an action_id)
- After `exec_command("git status")` succeeds, call `_emit_command_output(action_id, "git status", stdout, exit_code)`
- On failure, emit with stderr and exit_code

### Task 2: Add `_emit_command_output` to `git_commit`
**File:** `src/agent_on_call/orchestrator.py`
**Changes:**
- Capture action_id from `_emit_action` (change the call at line 405 to capture return value)
- After the `git add` + `git commit` sequence completes, emit `_emit_command_output` with the full combined output
- Include both the `git add` and `git commit` commands in the display

### Task 3: Add `_emit_command_output` to `git_push`
**File:** `src/agent_on_call/orchestrator.py`
**Changes:**
- Capture action_id from `_emit_action` at line 450
- After push completes, emit `_emit_command_output` with sanitized output
- On failure, emit with error output

### Task 4: Add `_emit_command_output` to `web_fetch`
**File:** `src/agent_on_call/orchestrator.py`
**Changes:**
- Capture action_id from `_emit_action` at line 504
- After fetch completes, emit `_emit_command_output` with command=`fetch <url>`, output=(truncated response), exit_code=0/1

### Task 5: Add `_emit_command_output` to `web_search`
**File:** `src/agent_on_call/orchestrator.py`
**Changes:**
- Capture action_id from `_emit_action` at line 487
- After search completes, emit `_emit_command_output` with command=`search "<query>"`, output=(result), exit_code=0/1

### Task 6: Update frontend `commandTools` set
**File:** `frontend/src/app/page.tsx`
**Changes:**
- Add `"web_fetch"` and `"web_search"` to the `commandTools` Set (line 183) so the agent_action handler creates "running" terminal entries for these tools too

### Task 7: Write backend tests
**File:** `tests/test_orchestrator.py`
**Changes:**
- Add tests verifying `_emit_command_output` is called for `git_status`, `git_commit`, `git_push`, `web_fetch`, `web_search`
- Mock `_room.local_participant.publish_data` and verify message structure

### Task 8: Update frontend tests
**File:** `frontend/src/app/components/TerminalPanel.test.tsx` (existing)
**Changes:**
- Add test case for web_fetch/web_search terminal entries

### Task 9: Playwright E2E screenshot
- Connect to a room, trigger agent tool execution
- Take screenshot showing terminal panel with real output entries

## Test-First Order
1. Write backend tests for tasks 1-5 (they should fail)
2. Implement tasks 1-5
3. Run backend tests (they should pass)
4. Write frontend test for task 6 (should fail)
5. Implement task 6
6. Run frontend tests
7. Playwright screenshot

## Dependencies
- None — this builds on existing infrastructure
