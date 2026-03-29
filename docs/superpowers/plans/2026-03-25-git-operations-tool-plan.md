# Git Operations Tool — Implementation Plan

**Date:** 2026-03-25
**Story:** #3 — Add git operations tool
**Spec:** `docs/superpowers/specs/2026-03-25-git-operations-tool-design.md`

## Tasks

### Task 1: Add git_token to Config

**Files:** `src/agent_on_call/config.py`, `tests/test_config.py`

1. Write tests first:
   - Test Config loads `GIT_TOKEN` env var when present
   - Test Config works when `GIT_TOKEN` is not set (defaults to None)
2. Add `git_token: str | None = None` field to `Config` dataclass
3. In `load_config()`, read `GIT_TOKEN` via `os.environ.get("GIT_TOKEN")`

### Task 2: Add credential injection helper to WorkspaceManager

**Files:** `src/agent_on_call/workspace.py`, `tests/test_workspace.py`

1. Write tests first:
   - Test `_inject_git_credentials` rewrites HTTPS GitHub URL with token
   - Test `_inject_git_credentials` handles non-GitHub HTTPS URLs
   - Test `_inject_git_credentials` passes SSH URLs through unchanged
   - Test `_inject_git_credentials` returns URL unchanged when no token
   - Test `_sanitize_git_output` replaces token in output
   - Test `_sanitize_git_output` handles None token (no-op)
2. Add `_inject_git_credentials(url: str, token: str | None) -> str` as module-level helper
3. Add `_sanitize_git_output(output: str, token: str | None) -> str` as module-level helper

### Task 3: Add git_clone tool

**Files:** `src/agent_on_call/orchestrator.py`, `tests/test_orchestrator.py`

1. Write tests first:
   - Test `git_clone` calls exec_command with correct git clone command
   - Test `git_clone` injects credentials for HTTPS URLs
   - Test `git_clone` with optional branch parameter
   - Test `git_clone` with optional path parameter
   - Test `git_clone` sanitizes output (no token in response)
   - Test `git_clone` with empty URL returns error
   - Test `git_clone` handles auth failure
   - Test `git_clone` uses timeout=120
2. Implement `git_clone` on OrchestratorAgent
3. Use `_inject_git_credentials` from workspace module
4. Use `_sanitize_git_output` on response

### Task 4: Add git_status tool

**Files:** `src/agent_on_call/orchestrator.py`, `tests/test_orchestrator.py`

1. Write tests first:
   - Test `git_status` calls `git status` via exec_command
   - Test `git_status` returns readable output
   - Test `git_status` handles no-workspace error
2. Implement `git_status` — simple delegation to `exec_command("git status")`

### Task 5: Add git_commit tool

**Files:** `src/agent_on_call/orchestrator.py`, `tests/test_orchestrator.py`

1. Write tests first:
   - Test `git_commit` runs `git add` then `git commit -m`
   - Test `git_commit` with specific file list
   - Test `git_commit` with default files="." (all changes)
   - Test `git_commit` handles nothing-to-commit case
   - Test `git_commit` with empty message returns error
2. Implement `git_commit`:
   - Run `git add {files}`
   - Run `git commit -m "{message}"`
   - Return commit summary

### Task 6: Add git_push tool

**Files:** `src/agent_on_call/orchestrator.py`, `tests/test_orchestrator.py`

1. Write tests first:
   - Test `git_push` calls `git push origin` by default
   - Test `git_push` with custom remote and branch
   - Test `git_push` sanitizes output (credential safety)
   - Test `git_push` handles auth failure
   - Test `git_push` handles rejection (non-fast-forward)
2. Implement `git_push` with output sanitization

### Task 7: Verify all acceptance criteria

1. Run full test suite: `pytest --cov -v`
2. Verify coverage >= 90% on new code
3. Check each AC against implementation

## Dependencies

- Shell command execution tool (completed, PR #7)
- WorkspaceManager `exec_command` method (exists)
- Config system (exists, needs minor addition)

## Risk

- Credential injection URL rewriting: must handle various URL formats (github.com, gitlab.com, custom hosts). Start with GitHub, extend later.
- Token sanitization: must be thorough — any missed occurrence leaks credentials to the LLM context.
