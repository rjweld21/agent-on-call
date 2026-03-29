# Terminal Panel Implementation Plan

## Overview

Create a new `TerminalPanel` React component that displays command execution output in a terminal-style panel, distinct from the conversation transcript and activity panel.

## Tasks

### Task 1: Create `TerminalPanel.tsx` component

**Test first:** `frontend/src/app/components/TerminalPanel.test.tsx`
- Test renders empty state message
- Test renders entries with command, output, exit code
- Test exit code styling (green=0, red=non-zero)
- Test collapse/expand toggle
- Test auto-scroll behavior

**Implementation:** `frontend/src/app/components/TerminalPanel.tsx`
- `TerminalEntry` interface: `{ id, timestamp, command, output, exitCode, status }`
- `TerminalPanelProps`: `{ entries: TerminalEntry[] }`
- Dark terminal theme (`#0d1117`), monospace font
- Collapsible header "Terminal Output" with entry count badge
- Each entry: `$ command` on one line, output below, exit code badge
- Running entries show a pulsing indicator
- Auto-scroll to bottom on new entries

### Task 2: Integrate into `page.tsx`

**Files:** `frontend/src/app/page.tsx`

- Import `TerminalPanel` and `TerminalEntry` type
- Add `terminalEntries` state: `useState<TerminalEntry[]>([])`
- In the existing `dataReceived` handler, when `msg.type === "agent_action"` and `action.tool` is a command tool (`exec_command`, `git_clone`, `git_commit`, `git_push`, `git_status`):
  - On `status === "started"`: create new `TerminalEntry` with `status: "running"`, command from summary
  - On `status === "completed"` or `status === "failed"`: update existing entry with output from detail
- Parse exit code from the detail string (regex: `/Exit code: (\d+)/`)
- Render `<TerminalPanel entries={terminalEntries} />` between ThinkingPanel and Transcript

### Task 3: Run tests

- `npm test` in frontend -- unit tests pass
- Verify existing tests still pass (ThinkingPanel, SettingsPanel, etc.)

## File Changes Summary

| File | Action |
|------|--------|
| `frontend/src/app/components/TerminalPanel.tsx` | **NEW** |
| `frontend/src/app/components/TerminalPanel.test.tsx` | **NEW** |
| `frontend/src/app/page.tsx` | MODIFY (add TerminalPanel, wire data) |

## Estimated Effort

Size L -- new component with styling, data wiring, and tests. ~3-4 hours.
