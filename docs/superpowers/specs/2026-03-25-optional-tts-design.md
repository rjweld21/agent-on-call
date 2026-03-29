# Optional TTS — Graceful Degradation Design Spec

**Date:** 2026-03-25
**Story:** #38 — Make TTS optional: graceful degradation when Cartesia unavailable

## Overview

When the Cartesia TTS API key is missing, invalid, or has expired credits, the agent should fall back to a text-only response mode instead of appearing unresponsive. The user sees a notification banner and agent responses stream directly to the transcript in real time.

## Design Decisions

### TTS Health Check on Session Start

Before building the session, perform a lightweight health check:

```python
async def _check_tts_available() -> tuple[bool, str]:
    """Returns (available, reason)."""
```

1. If `CARTESIA_API_KEY` is not set or empty: return `(False, "no_key")`
2. If key is set: attempt a minimal TTS synthesis (e.g., synthesize a single word "test")
   - Success: return `(True, "")`
   - HTTP 401/403: return `(False, "auth_failed")`
   - HTTP 402: return `(False, "no_credits")`
   - Timeout/network error: return `(False, "network_error")`

### Config Changes

`config.py` currently requires `CARTESIA_API_KEY` via `_require()`. Change:
- Make `cartesia_api_key` optional: `cartesia_api_key: str | None = None`
- Use `os.environ.get("CARTESIA_API_KEY")` instead of `_require("CARTESIA_API_KEY")`
- The rest of the system uses the health check result, not the config validation

### Session Builder Changes

`_build_session` in `main.py` needs a `tts_enabled: bool` parameter:

```python
def _build_session(model: str | None, tts_enabled: bool = True) -> AgentSession:
    tts = cartesia.TTS(api_key=...) if tts_enabled else None
    return AgentSession(
        stt=deepgram.STT(...),
        llm=_build_llm(model=model),
        tts=tts,
        vad=silero.VAD.load(...),
        ...
    )
```

When `tts=None`, LiveKit Agents SDK skips TTS and the LLM response text goes directly to the transcript via the existing transcription mechanism.

### Data Channel Notification

When TTS is unavailable, send a data channel message to the frontend:

```json
{
  "type": "tts_status",
  "available": false,
  "reason": "no_key" | "auth_failed" | "no_credits" | "network_error"
}
```

When TTS becomes available again (e.g., key updated mid-session via settings), send:
```json
{
  "type": "tts_status",
  "available": true,
  "reason": ""
}
```

### Frontend Banner

In `page.tsx`, listen for `tts_status` messages on the data channel and show a persistent, dismissible banner:

| Reason | Banner Text |
|---|---|
| `no_key` | "Voice responses unavailable. Add a Cartesia API key in settings for voice responses." |
| `auth_failed` | "Voice responses unavailable. Cartesia API key is invalid." |
| `no_credits` | "Voice responses unavailable. Cartesia account has no credits remaining." |
| `network_error` | "Voice responses unavailable. Could not reach Cartesia API." |

Banner styling: amber/warning color (#f59e0b background tint), dismiss button, sticky at top of AgentInterface.

### Transcript Streaming in Text-Only Mode

When TTS is disabled:
- Agent responses appear in the transcript immediately as the LLM generates them
- The existing `agentTranscriptions` from LiveKit should still work since the SDK emits transcription events from the LLM output even without TTS
- The "speaking" state indicator should show "responding" instead when in text-only mode
- No audio is generated for agent responses

### Mid-Session TTS Recovery

If the user updates the Cartesia API key via settings:
1. Frontend sends `settings_update` with new key (requires adding `cartesiaApiKey` to settings)
2. Backend re-runs health check with new key
3. If healthy: rebuild TTS plugin, update session, send `tts_status` available=true
4. Frontend hides the banner

For MVP, this is optional. The primary flow is: TTS status is determined at session start and remains for the session duration. Recovery can be added as a fast-follow.

### Orchestrator Changes

In `orchestrator.py`, update `ORCHESTRATOR_INSTRUCTIONS` to include awareness of text-only mode:

```
If TTS is unavailable, your responses will appear as text in the transcript only.
Keep responses well-formatted for reading. You do not need to change your behavior
significantly — just be aware the user is reading, not listening.
```

This instruction is conditionally appended when `tts_enabled=False`.

## File Structure

```
src/agent_on_call/config.py        — Make cartesia_api_key optional
src/agent_on_call/main.py          — TTS health check, conditional session build, data channel message
src/agent_on_call/orchestrator.py   — Conditional text-mode instruction append
frontend/src/app/page.tsx           — TTS status banner, transcript streaming awareness
tests/test_config.py                — Test optional cartesia key
tests/test_main.py                  — Test health check, text-only session build (new file)
frontend/src/app/test/tts-banner.test.tsx — E2E/unit test for banner (new file)
```

## Out of Scope

- Browser-based TTS fallback (Web Speech API)
- Alternative TTS providers (ElevenLabs, etc.)
- Making STT optional (microphone still required)
- Mid-session TTS recovery (fast-follow, not MVP)
