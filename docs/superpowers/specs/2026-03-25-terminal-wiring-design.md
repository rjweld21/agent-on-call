# Terminal Wiring Design — Story #57

## Problem

The terminal panel component exists and renders entries, but several tool methods in `orchestrator.py` do not emit `command_output` data channel messages. This means:

- `git_status`, `git_commit`, `git_push` only emit `agent_action` events (which carry truncated summaries), not full `command_output` messages.
- `web_fetch` and `web_search` emit `agent_action` events but nothing terminal-specific — the issue requests that `web_fetch` shows the URL being fetched.
- The frontend correctly handles both `agent_action` and `command_output` message types, but only receives `command_output` from `exec_command` and `git_clone`.

## Root Cause

When `_emit_command_output` was added (PR #29), it was wired into `exec_command` and `git_clone` but not into the other git tool methods or web tools that also run commands or produce output suitable for the terminal panel.

## Design

### Backend Changes (`orchestrator.py`)

Add `_emit_command_output()` calls to all command-executing tool methods:

1. **`git_status`** — Emit `command_output` with command=`git status`, output=stdout, exit_code.
2. **`git_commit`** — Emit `command_output` with command=`git add ... && git commit -m ...`, output=stdout, exit_code.
3. **`git_push`** — Emit `command_output` with command=`git push ...`, output=(sanitized stdout+stderr), exit_code.
4. **`web_fetch`** — Emit `command_output` with command=`fetch <url>`, output=(first 1KB of response or error), exit_code=0/1.
5. **`web_search`** — Emit `command_output` with command=`search "<query>"`, output=(result summary), exit_code=0/1.

Each tool method should:
- Generate an action ID at the start (reuse the existing `_emit_action` ID)
- Call `_emit_command_output` with the full output after the operation completes
- Use the same `command_id` so the frontend can correlate `agent_action` and `command_output` messages

### Frontend Changes (`page.tsx`)

The existing `command_output` listener (lines 237-264) already handles creating/updating terminal entries from `command_output` messages. **No frontend changes needed** — once the backend emits the messages, the terminal panel will display them.

The existing `agent_action` handler for terminal entries (lines 183-234) creates "running" entries for command tools. The `command_output` handler then updates those entries with the full output. The `commandTools` set already includes `exec_command`, `git_clone`, `git_commit`, `git_push`, `git_status`. We should add `web_fetch` and `web_search` to this set so they also get "running" entries.

### Error Display

Terminal output for failed commands already renders in the component — `exitCode !== 0` gets a red badge. The `_emit_command_output` call should set `exit_code` to the actual command exit code (or -1 for exceptions).

## Testing Strategy

### Unit Tests (Backend)
- Test each tool method emits `_emit_command_output` (mock `_room` and verify `publish_data` calls)
- Verify `command_output` messages have correct structure (id, command, output, exitCode, done)

### Unit Tests (Frontend)
- Verify `web_fetch` and `web_search` actions create terminal entries (add to `commandTools` set)

### E2E (Playwright)
- Screenshot showing terminal panel with git and command output after agent executes tools
