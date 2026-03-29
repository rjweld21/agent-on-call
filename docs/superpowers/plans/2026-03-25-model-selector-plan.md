# Model Selector — Implementation Plan

**Date:** 2026-03-25
**Story:** #25 — Add anthropic model selector to frontend
**Spec:** `docs/superpowers/specs/2026-03-25-model-selector-design.md`

## Tasks

### Task 1: Create ModelSelector component with tests

**Files:** `frontend/src/app/components/ModelSelector.tsx`, `frontend/src/app/components/ModelSelector.test.tsx`

1. Write tests first:
   - Renders a `<select>` element with 3 model options
   - Shows correct labels (Claude Haiku 4.5, Claude Sonnet 4.5, Claude Opus 4)
   - Default selection is claude-sonnet-4-5-20250514
   - Calls updateSetting on change
   - Reads current value from settings context
2. Create ModelSelector component:
   - Define ANTHROPIC_MODELS constant array: `{ value, label }[]`
   - Use `useSettings()` to read `model.anthropicModel` and `updateSetting`
   - Render styled `<select>` dropdown matching dark theme
3. Export ANTHROPIC_MODELS for reuse in validation

### Task 2: Integrate ModelSelector into SettingsPanel

**Files:** `frontend/src/app/components/SettingsPanel.tsx`, `frontend/src/app/components/SettingsPanel.test.tsx`

1. Write/update tests:
   - Settings panel renders ModelSelector in the Model section
   - Model section no longer shows "No settings available yet"
2. Import ModelSelector component
3. Replace the Model section placeholder with `<ModelSelector />`
4. Update existing SettingsPanel tests if needed

### Task 3: Pass model selection to token API

**Files:** `frontend/src/app/page.tsx`, `frontend/src/app/api/token/route.ts`

1. Write tests:
   - Token API accepts `model` query parameter
   - Token API embeds model in participant metadata
   - Token API rejects invalid model values
   - Token API defaults to claude-sonnet-4-5-20250514 if no model param
2. Update `connect()` in page.tsx to read model from settings and pass as query param
3. Update token route to:
   - Parse `model` from URL search params
   - Validate against allowed list
   - Include in participant metadata JSON

### Task 4: Backend reads model from participant metadata

**Files:** `src/agent_on_call/main.py`

1. Write tests (optional, may be integration-level):
   - `_build_llm` accepts model parameter
   - `_build_llm` uses provided model over env var
   - `_build_llm` falls back to env var when no model provided
2. Update `_build_llm(model: str | None = None)` to accept model parameter
3. In `orchestrator_session`, read participant metadata from the connected user
4. Extract model name and pass to `_build_llm`

### Task 5: E2E verification

1. Run frontend tests: `cd frontend && npx vitest run`
2. Run backend tests: `pytest --cov -v`
3. Verify each AC against implementation

## Dependencies

- Settings panel must exist (completed: #30)
- settings-context.tsx must support arbitrary key-value storage (already does)

## Risk

- Reading participant metadata timing: metadata must be available when `orchestrator_session` runs. The token API sets it at token generation time, so it should be available immediately.
- Model name format may change with Anthropic releases. Using full model IDs mitigates this.
