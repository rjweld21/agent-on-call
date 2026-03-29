# Clean Workspace Design — Story #59

## Problem

`WorkspaceManager` creates Docker containers with named volumes (`aoc-workspace-{name}`) that persist across sessions. When a user starts a new call, the previous workspace data (cloned repos, files) remains. Users expect a clean slate for each session.

## Current Behavior

1. `create_workspace(name)` creates a container with `volumes={volume_name: {"bind": "/workspace", "mode": "rw"}}`.
2. If a container named `aoc-ws-{name}` already exists, Docker raises a conflict error.
3. `delete_workspace(name)` exists but is never called automatically.
4. Volumes persist even after container removal.

## Design

### `WorkspaceManager` Changes (`workspace.py`)

Add a `clean` parameter (default `True`) to `create_workspace`:

```python
def create_workspace(self, name: str, clean: bool = True) -> str:
```

When `clean=True`:
1. Stop and remove any existing container named `aoc-ws-{name}`
2. Remove the existing volume `aoc-workspace-{name}` if it exists
3. Create fresh container and volume

When `clean=False`:
1. If container exists and is running, reuse it
2. If container exists but is stopped, start it
3. If no container exists, create fresh

This preserves backward compatibility (default is clean) while enabling future "resume workspace" functionality.

### `main.py` Changes

No changes needed for the default behavior. The `OrchestratorAgent.create_workspace` tool already calls `self._workspace.create_workspace(name)`, which will default to `clean=True`.

### `orchestrator.py` Changes

Add an optional `clean` parameter to the `create_workspace` function tool:

```python
@function_tool
async def create_workspace(self, context: RunContext, name: str, clean: bool = True) -> str:
    """Create a new isolated workspace for a project.

    Args:
        name: Short descriptive name like 'my-app' or 'data-analysis'.
        clean: If True (default), removes any existing workspace with the same name first.
    """
```

### Session Startup Behavior

For the open-source version: always start clean unless the workspace name is explicitly reused with `clean=False`. No UI changes needed for MVP — the default behavior changes to "always clean".

### Future: UI Workspace Indicator

Out of scope for this story. The AC mentions "Optional: UI shows workspace name/status" — this can be a follow-up.

## Testing Strategy

### Unit Tests (`test_workspace.py`)
- `create_workspace(name, clean=True)` removes existing container and volume before creating
- `create_workspace(name, clean=False)` reuses existing container if running
- `create_workspace(name, clean=False)` starts existing stopped container
- `create_workspace(name, clean=False)` creates fresh if nothing exists
- Default `clean=True` behavior

### Unit Tests (`test_orchestrator.py`)
- `create_workspace` tool passes `clean` parameter through

### E2E
- Not needed (no UI changes)
