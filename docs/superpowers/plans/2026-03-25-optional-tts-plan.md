# Optional TTS — Implementation Plan

**Date:** 2026-03-25
**Story:** #38 — Make TTS optional: graceful degradation when Cartesia unavailable
**Spec:** `docs/superpowers/specs/2026-03-25-optional-tts-design.md`

## Tasks

### Task 1: Make cartesia_api_key optional in Config

**Files:** `src/agent_on_call/config.py`, `tests/test_config.py`

1. Write tests first:
   - Test `load_config()` succeeds when CARTESIA_API_KEY is not set
   - Test `load_config()` succeeds when CARTESIA_API_KEY is set
   - Test Config.cartesia_api_key is None when env var missing
   - Test Config.cartesia_api_key has value when env var present
2. Change `cartesia_api_key` from `_require("CARTESIA_API_KEY")` to `os.environ.get("CARTESIA_API_KEY")`
3. Update Config dataclass: `cartesia_api_key: str | None = None`

### Task 2: Add TTS health check

**Files:** `src/agent_on_call/main.py`, `tests/test_main.py` (new)

1. Write tests first:
   - Test `_check_tts_available` returns (False, "no_key") when key is None/empty
   - Test `_check_tts_available` returns (True, "") when synthesis succeeds
   - Test `_check_tts_available` returns (False, "auth_failed") on 401/403
   - Test `_check_tts_available` returns (False, "no_credits") on 402
   - Test `_check_tts_available` returns (False, "network_error") on timeout/connection error
2. Implement `async def _check_tts_available(api_key: str | None) -> tuple[bool, str]`
3. Use Cartesia client to attempt minimal synthesis
4. Catch specific HTTP status codes and map to reason strings

### Task 3: Conditional session build (no TTS)

**Files:** `src/agent_on_call/main.py`, `tests/test_main.py`

1. Write tests first:
   - Test `_build_session` with `tts_enabled=True` includes Cartesia TTS
   - Test `_build_session` with `tts_enabled=False` passes `tts=None`
   - Test `orchestrator_session` calls health check and builds session accordingly
2. Add `tts_enabled: bool = True` parameter to `_build_session`
3. When `tts_enabled=False`: pass `tts=None` to AgentSession
4. In `orchestrator_session`: call health check, pass result to `_build_session`

### Task 4: Send TTS status via data channel

**Files:** `src/agent_on_call/main.py`, `tests/test_main.py`

1. Write tests first:
   - Test tts_status message is published when TTS unavailable
   - Test tts_status message format includes available and reason fields
   - Test no tts_status message when TTS is available
2. After session start, if TTS unavailable: publish data channel message
3. Message format: `{"type": "tts_status", "available": false, "reason": "<reason>"}`

### Task 5: Conditional orchestrator instructions

**Files:** `src/agent_on_call/orchestrator.py`, `tests/test_orchestrator.py`

1. Write tests first:
   - Test text-only instruction append when tts_enabled=False
   - Test normal instructions when tts_enabled=True
2. Add `tts_enabled` parameter to OrchestratorAgent constructor (or set via attribute)
3. Append text-mode awareness instruction when TTS is disabled

### Task 6: Frontend TTS status banner

**Files:** `frontend/src/app/page.tsx`, `frontend/src/app/test/tts-banner.test.tsx` (new)

1. Write tests first:
   - Test banner appears when tts_status message received with available=false
   - Test banner shows correct text for each reason
   - Test banner is dismissible
   - Test banner hides when tts_status available=true received
   - Test no banner shown when TTS is available
2. Add state: `ttsBanner: { visible: boolean, reason: string } | null`
3. Listen for `tts_status` data channel messages in the existing `_on_data_received` pattern
4. Render amber banner at top of AgentInterface when visible
5. Include dismiss button

### Task 7: Update transcript streaming awareness

**Files:** `frontend/src/app/page.tsx`

1. When TTS unavailable, the "speaking" state label should show "responding" instead
2. Agent responses still flow through `agentTranscriptions` — LiveKit SDK handles this
3. Verify transcript updates are real-time (no dependency on TTS completion)

### Task 8: Verify all acceptance criteria

1. Run backend tests: `pytest --cov -v`
2. Run frontend tests: `npm test`
3. Run Playwright E2E tests for banner visibility
4. Check each AC against implementation

## Dependencies

- Existing orchestrator voice pipeline (main.py)
- LiveKit data channel (already used for settings)
- Cartesia SDK for health check

## Risk

- LiveKit SDK behavior with `tts=None`: need to verify AgentSession accepts None for TTS and still streams LLM text to transcriptions. If not, may need a no-op TTS adapter.
- Health check adds latency to session start: keep it fast (short timeout, small payload).
