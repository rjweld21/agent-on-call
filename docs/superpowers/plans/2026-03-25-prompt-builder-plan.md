# Basic PromptBuilder Implementation Plan

## Overview

Create a `PromptBuilder` class to replace ad-hoc prompt string concatenation in `main.py` with a structured, token-budget-aware approach.

## Tasks

### Task 1: Create `src/agent_on_call/prompt_builder.py`

**Test first:** `tests/test_prompt_builder.py`
- Test `PromptBuilder.build()` returns base instructions
- Test verbosity directive is appended
- Test TTS text mode note is included when `set_tts_available(False)`
- Test token budget enforcement via `estimate_tokens()`
- Test truncation order: workspace info dropped before tools, tools before verbosity

**Implementation:**
- `PromptBuilder` class with builder-pattern setters
- `VERBOSITY_PROMPTS` dict (moved from `main.py`)
- `TEXT_MODE_INSTRUCTION` constant (moved from `main.py`)
- `build()` method that assembles sections with priority-based truncation
- `estimate_tokens()` static method (`len(text) // 4`)

### Task 2: Integrate into `main.py`

**Files:** `src/agent_on_call/main.py`

- Import `PromptBuilder` from `prompt_builder`
- Remove `VERBOSITY_PROMPTS` dict (now in `prompt_builder.py`)
- Remove `TEXT_MODE_INSTRUCTION` constant (now in `prompt_builder.py`)
- Remove `_build_verbosity_instructions()` function
- Create `PromptBuilder` instance in `orchestrator_session()`
- Use `prompt_builder.build()` for initial instructions
- Use `prompt_builder.set_verbosity()` + `.build()` in `_apply_settings_update()`
- Use `prompt_builder.set_tts_available(False)` + `.build()` in `_disable_tts_runtime()`

### Task 3: Update `orchestrator.py`

**Files:** `src/agent_on_call/orchestrator.py`

- `ORCHESTRATOR_INSTRUCTIONS` stays in `orchestrator.py` (it's the base content)
- No changes to `OrchestratorAgent` class itself

### Task 4: Update existing tests

**Files:** `tests/test_main.py`

- Update any tests that reference `_build_verbosity_instructions` or `VERBOSITY_PROMPTS`
- Add integration-style tests verifying `PromptBuilder` is used correctly in session setup

### Task 5: Run all tests, verify Docker build

- `pytest tests/` -- all pass
- Docker build succeeds
- Verify no regressions in existing test suite

## File Changes Summary

| File | Action |
|------|--------|
| `src/agent_on_call/prompt_builder.py` | **NEW** |
| `tests/test_prompt_builder.py` | **NEW** |
| `src/agent_on_call/main.py` | MODIFY (remove old functions, use PromptBuilder) |
| `tests/test_main.py` | MODIFY (update references) |
| `src/agent_on_call/orchestrator.py` | NO CHANGE |

## Estimated Effort

Size M -- straightforward refactor with new module, ~2-3 hours including tests.
