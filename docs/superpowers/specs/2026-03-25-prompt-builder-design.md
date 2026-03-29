# Basic PromptBuilder Design

## Problem

The orchestrator's system prompt (`ORCHESTRATOR_INSTRUCTIONS`) is a static string in `orchestrator.py`. Verbosity directives are appended in `main.py` via `_build_verbosity_instructions()`, and TTS status is also appended there. This approach is fragile:

- Adding new prompt sections means touching multiple files
- No token budget enforcement
- No structured way to compose runtime context (active tools, workspace state)
- The verbosity/TTS patching in `main.py` is ad-hoc string concatenation

## Scope (Open-Source Basic Version)

Only implement the basic version:
1. **PromptBuilder** class that composes: base instructions + verbosity directive + active state (tools, workspace)
2. **Token budget management** (configurable, default ~1500 tokens)
3. **Replace** the current `_build_verbosity_instructions` approach in `main.py`

NOT in scope (managed service features):
- Project profile section
- Session summary section

## Design

### PromptBuilder Class

```python
# src/agent_on_call/prompt_builder.py

class PromptBuilder:
    """Composes the orchestrator system prompt from structured sections."""

    def __init__(self, token_budget: int = 1500):
        self._token_budget = token_budget
        self._base_instructions: str = ""
        self._verbosity: int = 3
        self._tts_available: bool = True
        self._active_tools: list[str] = []
        self._workspace_info: str | None = None

    def set_base_instructions(self, instructions: str) -> "PromptBuilder":
        """Set the fixed base instructions (always included)."""

    def set_verbosity(self, level: int) -> "PromptBuilder":
        """Set verbosity level (1-5)."""

    def set_tts_available(self, available: bool) -> "PromptBuilder":
        """Set TTS availability status."""

    def set_active_tools(self, tools: list[str]) -> "PromptBuilder":
        """Set list of active tool names for context."""

    def set_workspace_info(self, info: str | None) -> "PromptBuilder":
        """Set current workspace status summary."""

    def build(self) -> str:
        """Compose all sections into a final prompt string within token budget."""

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Rough token estimate: len(text) / 4."""
```

### Section Priority (for truncation)

When the total exceeds the token budget, truncate in this order (lowest priority first):
1. Workspace info (can be omitted)
2. Active tools list (can be omitted)
3. Verbosity directive (compact but important)
4. Base instructions (never truncated -- always present in full)

### Integration with main.py

Replace the current pattern:
```python
# BEFORE (main.py)
agent._instructions = _build_verbosity_instructions(base_instructions, verbosity)
```

With:
```python
# AFTER (main.py)
prompt_builder = PromptBuilder(token_budget=1500)
prompt_builder.set_base_instructions(ORCHESTRATOR_INSTRUCTIONS)
prompt_builder.set_verbosity(verbosity)
prompt_builder.set_tts_available(tts_available)
agent._instructions = prompt_builder.build()
```

Mid-session updates (verbosity change, TTS disable) call `prompt_builder.set_*()` then `prompt_builder.build()`.

### VERBOSITY_PROMPTS

Move `VERBOSITY_PROMPTS` dict from `main.py` into `prompt_builder.py` since it's logically part of prompt composition.

### Token Budget

- Default: 1500 tokens (~6000 characters)
- Base instructions: ~400 tokens (always included)
- Verbosity directive: ~30-60 tokens
- TTS text mode note: ~50 tokens (when TTS unavailable)
- Active tools: ~20 tokens per tool
- Workspace info: variable, capped at remaining budget

## Testing Strategy

Unit tests in `tests/test_prompt_builder.py`:
- `test_build_includes_base_instructions`
- `test_build_includes_verbosity_directive`
- `test_build_includes_tts_text_mode`
- `test_build_omits_tts_note_when_available`
- `test_build_within_token_budget`
- `test_truncation_order` (workspace info dropped first)
- `test_missing_sections_graceful`
- `test_estimate_tokens`
- `test_set_verbosity_validates_range`
- `test_mid_session_rebuild`
