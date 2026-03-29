# Enhanced Activity Log — Implementation Plan

**Date:** 2026-03-25
**Story:** #36 — Enhance thinking panel: show real agent actions and command summaries
**Spec:** `docs/superpowers/specs/2026-03-25-enhanced-activity-log-design.md`

## Tasks

### Task 1: Add _emit_action method to OrchestratorAgent

**Files:** `src/agent_on_call/orchestrator.py`, `tests/test_orchestrator.py`

1. Write tests first:
   - Test _emit_action publishes JSON to data channel with correct format
   - Test _emit_action silently no-ops when room is None
   - Test _emit_action includes all required fields (id, kind, tool, summary, status, timestamp)
2. Add `_room` attribute to OrchestratorAgent (default None)
3. Add `set_room(room)` method
4. Implement `_emit_action(kind, tool, summary, detail, status)` using `self._room.local_participant.publish_data()`

### Task 2: Instrument existing function_tools with action events

**Files:** `src/agent_on_call/orchestrator.py`, `tests/test_orchestrator.py`

1. Write tests first:
   - Test exec_command emits "started" then "completed" actions
   - Test exec_command emits "failed" on error
   - Test create_workspace emits action
   - Test read_file emits action
   - Test write_file emits action
   - Test list_files emits action
2. Add `_emit_action` calls to each `@function_tool` method:
   - Before execution: status="started"
   - After success: status="completed"
   - After failure: status="failed"
3. Summary should be human-readable (e.g., "Running: git clone ..." not the raw command)

### Task 3: Pass room reference from main.py

**Files:** `src/agent_on_call/main.py`

1. In `orchestrator_session`, after `session.start()`, call `agent.set_room(ctx.room)`
2. This enables action event publishing

### Task 4: Update ThinkingPanel with collapsible detail and status

**Files:** `frontend/src/app/components/ThinkingPanel.tsx`, `frontend/src/app/test/thinking-panel.test.tsx`

1. Write tests first:
   - Test activity item with detail shows expand/collapse toggle
   - Test clicking toggle shows/hides detail content
   - Test status="started" shows spinner indicator
   - Test status="completed" shows checkmark
   - Test status="failed" shows error indicator
   - Test activity without detail shows no toggle
2. Update ActivityItem interface: add `tool`, `status`, `expanded` fields
3. Add click handler to toggle `expanded` state per item
4. Add status indicators (CSS-based, no external icons)
5. Increase maxHeight from 180px to 250px

### Task 5: Add data channel listener for agent_action in page.tsx

**Files:** `frontend/src/app/page.tsx`

1. Write tests first:
   - Test agent_action message adds activity to panel
   - Test agent_action with existing ID updates activity in-place
   - Test non-agent_action messages are ignored
2. Add handler for `agent_action` messages in the data channel listener
3. Map incoming action to ActivityItem format
4. Handle status updates (started -> completed) by matching action ID
5. Remove synthetic state-based activity generation (the useEffect that creates "Processing..." items)

### Task 6: Verify all acceptance criteria

1. Run backend tests: `pytest --cov -v`
2. Run frontend tests: `npm test`
3. Run Playwright E2E: verify actions appear in thinking panel during agent work
4. Check each AC against implementation

## Dependencies

- Existing ThinkingPanel component (PR #10)
- LiveKit data channel (already used for settings)
- Shell command execution tool (PR #7) — actions to surface

## Risk

- Room reference timing: `_emit_action` may be called before `set_room`. The no-op guard handles this.
- Data channel message ordering: LiveKit delivers in order per topic, so actions should appear chronologically.
- Action event volume: frequent tool calls may flood the panel. The existing maxHeight + scroll handles this.
