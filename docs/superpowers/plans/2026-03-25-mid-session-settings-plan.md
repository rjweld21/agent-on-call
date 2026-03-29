# Mid-Session Settings Implementation Plan

**Date:** 2026-03-25
**Story:** #37 — Apply model and verbosity changes mid-session without restart
**Branch:** `feat/mid-session-settings`

## Task Breakdown

### Task 1: Agent-side data channel handler (main.py)

**Test first:** `tests/test_data_channel.py`
- Test that `_handle_settings_update` correctly parses valid JSON
- Test that invalid JSON is ignored gracefully
- Test that invalid model names are rejected
- Test that verbosity out of range (0, 6, -1) is rejected
- Test that valid model + verbosity updates are applied

**Implementation:**
- In `main.py`, after `session.start()`, register a data received handler on `ctx.room`
- Handler function `_handle_settings_update(data_packet)`:
  - Parse JSON from `data_packet.data`
  - Check `type == "settings_update"`
  - Validate model against `VALID_ANTHROPIC_MODELS`
  - Validate verbosity is int 1-5
  - For verbosity: rebuild instructions string with new directive, call `session.update_instructions()` or update `agent._raw_instructions`
  - For model: call `_build_llm(new_model)` and update session LLM
  - Publish acknowledgment back via `ctx.room.local_participant.publish_data()`

**Files:** `src/agent_on_call/main.py`, `tests/test_data_channel.py`

### Task 2: Frontend data channel sender (settings-context.tsx)

**Test first:** `frontend/src/lib/settings-context.test.tsx`
- Test that `useSettingsSync` hook calls `publishData` when settings change
- Test debounce behavior (rapid changes only send last value)
- Test that sync is not called before room is set

**Implementation:**
- In `settings-context.tsx`, add a new hook `useSettingsSync(room)` that:
  - Watches `settings.model.anthropicModel` and `settings.voice.verbosity`
  - On change, debounces 300ms, then calls `room.localParticipant.publishData(JSON.stringify({...}))`
  - Returns void; purely a side-effect hook

**Files:** `frontend/src/lib/settings-context.tsx`, `frontend/src/lib/settings-context.test.tsx`

### Task 3: Wire up data channel in page.tsx

**Test first:** `frontend/src/app/test/page.test.tsx` (extend existing)
- Test that `useSettingsSync` is called with the room when connected
- Test that settings acknowledgment from agent updates UI indicator

**Implementation:**
- In `AgentInterface` component in `page.tsx`:
  - Get room from `useRoomContext()` (from @livekit/components-react)
  - Call `useSettingsSync(room)` to wire up data channel sending
  - Listen for `settings_ack` data messages to show confirmation indicator
  - Add a small status indicator near settings button showing "Settings synced" briefly

**Files:** `frontend/src/app/page.tsx`

### Task 4: E2E test

**Test first:** `frontend/e2e/mid-session-settings.spec.ts`
- Navigate to app, verify settings panel opens
- Change model and verbosity
- Verify data channel message is sent (mock or intercept)
- Note: Full E2E with agent requires running agent backend; may be limited to frontend-only E2E

**Files:** `frontend/e2e/mid-session-settings.spec.ts`

## Implementation Order

1. Task 1 (agent handler) — can be developed independently
2. Task 2 (frontend hook) — can be developed independently
3. Task 3 (wire up) — depends on Task 2
4. Task 4 (E2E) — depends on Tasks 1-3

## Existing Code to Reuse

- `_build_llm()` in `main.py` — already handles model parameter
- `VERBOSITY_PROMPTS` in `main.py` — already has prompt strings per level
- `VALID_ANTHROPIC_MODELS` in `main.py` — validation set
- `useSettings()` hook in `settings-context.tsx` — already tracks settings state
- `useLocalParticipant()` from LiveKit — for data channel access

## Risk

- LiveKit Agents Python SDK may not support `session.update_instructions()` or LLM hot-swap. If not, we store pending settings and apply them by modifying the agent's state before the next inference call. This is the primary implementation risk and should be investigated first in Task 1.
