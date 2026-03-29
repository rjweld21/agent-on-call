# Enhanced Activity Log — Design Spec

**Date:** 2026-03-25
**Story:** #36 — Enhance thinking panel: show real agent actions and command summaries

## Overview

The current ThinkingPanel shows generic "Processing..." and "Responding to user" states based on agent state transitions. This enhancement surfaces real agent actions — tool calls, commands executed, file operations — in real time via LiveKit data channel messages from the orchestrator backend.

## Design Decisions

### Data Flow: Agent -> Frontend

The orchestrator emits action events via LiveKit data channel whenever a function_tool is invoked:

```
orchestrator.py (tool call)
  -> data channel message (JSON)
  -> page.tsx (listener)
  -> ThinkingPanel (activities state)
```

### Data Channel Message Format

```json
{
  "type": "agent_action",
  "action": {
    "id": "action-<timestamp>-<random>",
    "kind": "tool_call" | "executing" | "result" | "thinking",
    "tool": "exec_command" | "git_clone" | "read_file" | ...,
    "summary": "Cloning repository example/repo...",
    "detail": "git clone https://github.com/example/repo /workspace/repo",
    "status": "started" | "completed" | "failed",
    "timestamp": "<ISO 8601>"
  }
}
```

Fields:
- `kind`: maps directly to ActivityType in ThinkingPanel
- `tool`: the function_tool name (for icon/color selection)
- `summary`: human-readable one-liner (shown by default)
- `detail`: full command or output (shown when expanded)
- `status`: lifecycle state — `started` means in progress, `completed`/`failed` means done

### Orchestrator Emitter

Add a helper method to OrchestratorAgent that publishes action events:

```python
async def _emit_action(self, kind: str, tool: str, summary: str, detail: str = "", status: str = "started"):
```

Each `@function_tool` method calls `_emit_action` before and after execution:
1. Before: `_emit_action("executing", "exec_command", "Running: ls -la", status="started")`
2. After: `_emit_action("result", "exec_command", "Command completed (exit 0)", detail=truncated_output, status="completed")`

The emitter needs access to the room's local_participant to publish data. This requires passing the room reference to the agent, which can be done during session setup.

### Room Reference in OrchestratorAgent

Add a `set_room(room)` method or accept it in constructor. The `orchestrator_session` in main.py calls `agent.set_room(ctx.room)` after session start. The `_emit_action` method uses `self._room.local_participant.publish_data()`.

If `_room` is None (before session start), `_emit_action` silently no-ops.

### ThinkingPanel Enhancements

1. **Collapsible detail**: Each ActivityItem gains a toggleable detail section
2. **Status indicator**: Spinner for "started", checkmark for "completed", X for "failed"
3. **Tool-specific icons**: Command (terminal icon), git (branch icon), file (document icon), thinking (brain icon)
4. **Real-time updates**: Started items update in-place when completed/failed (match by action ID)
5. **Increased max-height**: From 180px to 250px for better visibility

### ActivityItem Type Updates

```typescript
export interface ActivityItem {
  id: string;
  type: ActivityType;
  text: string;
  timestamp: Date;
  detail?: string;
  tool?: string;        // NEW: function_tool name
  status?: "started" | "completed" | "failed";  // NEW: lifecycle
  expanded?: boolean;   // NEW: UI state for detail toggle
}
```

### page.tsx Changes

Add listener for `agent_action` data channel messages alongside existing `settings_update`:

```typescript
// In AgentInterface, add to data channel handler:
if (msg.type === "agent_action") {
  const action = msg.action;
  setActivities(prev => {
    // If action has matching ID with status update, replace it
    const existing = prev.findIndex(a => a.id === action.id);
    if (existing >= 0) {
      const updated = [...prev];
      updated[existing] = { ...updated[existing], ...mapAction(action) };
      return updated;
    }
    // New action
    return [...prev, mapAction(action)];
  });
}
```

### Remove Synthetic State-Based Activities

Currently page.tsx generates fake "Processing..." and "Responding to user" activities from state transitions. With real action events, remove this synthetic generation. The ThinkingPanel should only show actual tool calls and results.

## File Structure

```
src/agent_on_call/orchestrator.py         — Add _emit_action, instrument all function_tools
frontend/src/app/components/ThinkingPanel.tsx — Collapsible detail, status indicators, tool icons
frontend/src/app/page.tsx                  — Data channel listener for agent_action, remove synthetic activities
tests/test_orchestrator.py                 — Test _emit_action calls in each tool
frontend/src/app/test/thinking-panel.test.tsx — Test collapsible detail, status updates
```

## Out of Scope

- Full terminal emulator
- Editing/interacting with commands from the panel
- Historical action log across sessions
- Filtering/searching actions
