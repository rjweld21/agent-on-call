# Model Selector — Design Spec

**Date:** 2026-03-25
**Story:** #25 — Add anthropic model selector to frontend

## Overview

Add a dropdown/selector in the frontend settings panel that lets users choose which Anthropic model the orchestrator uses. The selection is persisted in localStorage and sent to the backend when a session starts.

## Design Decisions

### Available Models

The selector shows Anthropic models available through the LiveKit Anthropic plugin:
- `claude-haiku-4-5-20250514` — Fast, lightweight (label: "Claude Haiku 4.5")
- `claude-sonnet-4-5-20250514` — Balanced (label: "Claude Sonnet 4.5")
- `claude-opus-4-20250514` — Most capable (label: "Claude Opus 4")

Default: `claude-sonnet-4-5-20250514` (matches current env var default `claude-sonnet-4-20250514`; updating to latest).

### How the Selection Reaches the Backend

The frontend sends the selected model as a query parameter when requesting the LiveKit token:
```
GET /api/token?model=claude-sonnet-4-5-20250514
```

The token API includes the model in the room metadata or participant metadata. The agent reads this metadata on session start and uses it to construct the LLM.

**Alternative considered:** LiveKit data channel message after connection. Rejected because the LLM must be configured before the first agent response, and the session is created in the `@server.rtc_session` handler before any data messages arrive.

**Implementation approach:**
1. Frontend sends model choice as query param to `/api/token`
2. Token API embeds the model in the participant's metadata (JSON: `{"model": "claude-sonnet-4-5-20250514"}`)
3. The agent reads participant metadata from `ctx.room` in the `rtc_session` handler
4. `_build_llm()` accepts the model name as a parameter instead of reading `ANTHROPIC_MODEL` env var

### Settings Panel Integration

The model selector lives in the "Model" section of the existing SettingsPanel component. It replaces the "No settings available yet" placeholder.

Component structure:
- `ModelSelector` — a `<select>` dropdown with model options
- Uses `useSettings()` hook to read/write `model.anthropicModel`
- Styled consistently with the settings panel dark theme

### Persistence

- Stored in settings context under `model.anthropicModel`
- Persisted to localStorage via the existing SettingsProvider mechanism
- On page load, the last-used model is pre-selected
- Default value if nothing stored: `claude-sonnet-4-5-20250514`

### Token API Changes

`frontend/src/app/api/token/route.ts`:
- Accept `model` query parameter
- Include in participant metadata: `JSON.stringify({ model: modelParam })`
- Validate model is one of the allowed values (reject unknown models)

### Backend Changes

`src/agent_on_call/main.py`:
- In `orchestrator_session`, read model from room participant metadata
- Pass model to `_build_llm(model=...)` instead of using env var
- Fall back to env var `ANTHROPIC_MODEL` if no metadata is present (backward compatible)

## File Structure

```
frontend/src/app/components/ModelSelector.tsx           — New component
frontend/src/app/components/ModelSelector.test.tsx       — Unit tests
frontend/src/app/components/SettingsPanel.tsx            — Import and render ModelSelector in Model section
frontend/src/app/api/token/route.ts                     — Accept model query param, embed in metadata
frontend/src/app/page.tsx                               — Pass model from settings to connect()
frontend/src/lib/settings-context.tsx                   — No changes (already supports arbitrary keys)
src/agent_on_call/main.py                              — Read model from metadata, pass to _build_llm
tests/test_orchestrator.py                             — Test model parameter handling (optional)
```

## Out of Scope

- Switching models mid-conversation
- OpenAI model selection (separate story)
- Cost estimation display
- Model capability descriptions in UI
