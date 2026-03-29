# Git Operations Tool — Design Spec

**Date:** 2026-03-25
**Story:** #3 — Add git operations tool

## Overview

Add dedicated `@function_tool` methods to OrchestratorAgent for common git operations: clone, status, commit, and push. Each tool delegates to `WorkspaceManager.exec_command()` with the appropriate git command string. Credential injection uses environment variables (e.g., `GIT_TOKEN`) to rewrite HTTPS URLs, and credentials are never exposed in tool responses.

## Design Decisions

### Separate Tools vs. Generic exec_command

The agent already has `exec_command` which can run arbitrary git commands. Dedicated git tools provide:
1. **Credential injection** — automatic token insertion into clone URLs without the LLM handling secrets
2. **Structured output** — parsed, human-readable results instead of raw git output
3. **Safety** — credentials are stripped from all responses before reaching the LLM
4. **Discoverability** — the LLM sees named tools (`git_clone`, `git_status`, etc.) in its tool list

### Tool Signatures

```python
@function_tool
async def git_clone(self, context: RunContext, repo_url: str, branch: str = "", path: str = "") -> str:
    """Clone a git repository into the workspace."""

@function_tool
async def git_status(self, context: RunContext) -> str:
    """Show the git working tree status."""

@function_tool
async def git_commit(self, context: RunContext, message: str, files: str = ".") -> str:
    """Stage files and commit with a message."""

@function_tool
async def git_push(self, context: RunContext, remote: str = "origin", branch: str = "") -> str:
    """Push commits to a remote repository."""
```

### Credential Injection Strategy

1. `WorkspaceManager` gets a new method `_inject_git_credentials(url: str) -> str` (private, not exposed to LLM).
2. For HTTPS URLs: if `GIT_TOKEN` env var is set, rewrite `https://github.com/...` to `https://{token}@github.com/...`.
3. For SSH URLs: no rewriting needed — rely on SSH keys mounted into the container.
4. The credential injection happens inside the tool implementation, not in the LLM prompt.
5. The `Config` dataclass gets an optional `git_token: str | None` field, loaded from `GIT_TOKEN` env var.

### Credential Safety

Every tool response passes through a `_sanitize_git_output(output: str, token: str | None) -> str` helper that:
- Replaces any occurrence of the git token with `***`
- Strips `Authorization:` headers from verbose output
- This runs on both stdout and stderr before returning to the LLM

### Error Handling

| Scenario | Behavior |
|---|---|
| No workspace active | Return "No active workspace. Create one first." |
| Auth failure (401/403) | Return "Authentication failed. Check GIT_TOKEN." |
| Clone into non-empty dir | Return clear error, suggest a different path |
| Merge conflicts on push | Return conflict message, suggest user resolve |
| Network timeout | Return timeout error via existing exec_command timeout |

### git_clone Flow

1. Validate `repo_url` is non-empty
2. Inject credentials: `_inject_git_credentials(repo_url)`
3. Build command: `git clone {branch_flag} {credentialed_url} {path}`
4. Execute via `exec_command` with timeout=120 (clones can be slow)
5. Sanitize output, return success/failure message

### git_commit Flow

1. Run `git add {files}` (default: `.` for all changes)
2. Run `git commit -m "{message}"`
3. Return commit hash and summary
4. If nothing to commit, return informative message

### git_push Flow

1. Run `git push {remote} {branch}` (defaults: origin, current branch)
2. Sanitize output (may contain token in remote URL)
3. Return success/failure with remote output

## File Structure

```
src/agent_on_call/orchestrator.py  — Add git_clone, git_status, git_commit, git_push tools
src/agent_on_call/workspace.py     — Add _inject_git_credentials helper
src/agent_on_call/config.py        — Add optional git_token field
tests/test_orchestrator.py         — Tests for all git tools (mock exec_command)
tests/test_workspace.py            — Test credential injection
tests/test_config.py               — Test git_token loading
```

## Out of Scope

- Branch management (checkout, merge, rebase)
- Merge conflict resolution
- Git hooks configuration
- PR creation (separate story)
- SSH key management
