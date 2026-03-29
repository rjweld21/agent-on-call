# Rich Activity Events Design — Story #58

## Problem

The ThinkingPanel shows basic events but lacks consistent, descriptive human-readable summaries. Some tools (`list_workspaces`) don't emit activity events at all. The `started` -> `completed`/`failed` lifecycle is inconsistent across tools.

## Current State (after #57 merge)

| Tool | Emits Started? | Emits Completed? | Summary Quality |
|------|---------------|-----------------|-----------------|
| create_workspace | Yes (tool_call) | Yes | Good |
| exec_command | Yes (executing) | Yes | Good |
| read_file | Yes (tool_call) | Yes | Okay — no action_id threading |
| write_file | Yes (tool_call) | Yes | Okay — no action_id threading |
| list_files | Yes (tool_call) | Yes | Okay — no action_id threading |
| list_workspaces | No | No | Missing entirely |
| git_clone | Yes (executing) | Yes | Good |
| git_status | Yes (tool_call) | Yes | Good |
| git_commit | Yes (executing) | Yes | Good |
| git_push | Yes (executing) | Yes | Good |
| web_search | Yes (tool_call) | Yes | Good |
| web_fetch | Yes (tool_call) | Yes | Good |
| analyze_codebase | Yes (tool_call) | Yes | Good |

## Design

### Consistency Changes

1. **All tools emit started + completed/failed events** — add events to `list_workspaces`
2. **Thread action_id through all tools** — `read_file`, `write_file`, `list_files` currently don't capture the action_id from `_emit_action` and pass it to the completion event
3. **Use consistent `kind` values**: Use `"executing"` for tools that run commands/operations, `"tool_call"` for data-access tools
4. **Improve summaries** to match the issue spec format:
   - exec_command: "Running command: {short description}" (already good)
   - git_clone: "Cloning repository: {url}" (change from "Cloning: {url}")
   - git_commit: "Committing changes: {message}" (change from "Committing: {msg}")
   - web_search: "Searching the web: {query}" (change from "Searching: {query}")
   - read_file: "Reading file: {path}" (change from "Reading: {path}")
   - write_file: "Writing file: {path}" (change from "Writing: {path}")
   - list_files: "Listing directory: {path}" (change from "Listing: {path}")
   - analyze_codebase: "Analyzing project structure" (change from "Analyzing: {path}")

### Action ID Threading

For consistent frontend correlation, every tool should:
1. Capture `action_id = await self._emit_action(...)` on the start event
2. Pass `action_id=action_id` on the completion/failure event

## Testing Strategy

### Unit Tests
- Test that `list_workspaces` now emits activity events
- Test that `read_file`, `write_file`, `list_files` thread action_id correctly
- Test that all tools use the new summary format
