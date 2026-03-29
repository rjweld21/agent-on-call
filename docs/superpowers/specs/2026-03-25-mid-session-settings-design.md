# Mid-Session Settings Design

**Date:** 2026-03-25
**Story:** #37 — Apply model and verbosity changes mid-session without restart

## Problem

Settings (model, verbosity) are baked into the LiveKit token at session start via the token API. Changing them requires leaving and rejoining the call, creating a disruptive user experience.

## Constraints

- LiveKit Agents v1.4 — must use framework-supported communication patterns
- Current response must finish naturally before changes take effect
- No call interruption or reconnection allowed
- Frontend already has settings panel, model selector, and verbosity slider (PRs #5, #8, #9 merged)

## Approach: LiveKit Data Channel

Use LiveKit's **data channel** to send setting updates from the frontend to the agent. This is preferred over RPC (not widely supported in the Agents Python SDK) and room metadata (event-driven but heavier and visible to all participants).

### Communication Flow

```
Frontend (settings-context.tsx)
  --> useEffect watches settings changes
  --> room.localParticipant.publishData(JSON.stringify({ type: "settings_update", model, verbosity }))

Agent (main.py)
  --> ctx.room.on("data_received", handler)
  --> handler parses JSON, applies changes
```

### Frontend Changes (settings-context.tsx, page.tsx)

1. **settings-context.tsx**: Add a `sendSettingsToAgent` callback that publishes settings via the LiveKit data channel. The context needs access to the LiveKit room, so we add an optional `room` property that page.tsx sets when connected.
2. **page.tsx**: After LiveKit room connects, wire up the room reference to the settings context so it can publish data channel messages. Watch for settings changes and send updates.

### Agent Changes (main.py, orchestrator.py)

1. **main.py**: Register a `data_received` handler on `ctx.room` that:
   - Parses incoming JSON messages
   - For model changes: rebuilds the LLM plugin via `_build_llm(new_model)` and calls `session.update_llm(new_llm)` (if supported) or stores pending and applies on next turn
   - For verbosity changes: updates the agent instructions via `agent._raw_instructions` or `session.update_instructions()` with the new verbosity directive
2. **orchestrator.py**: No structural changes needed. The instructions are already a string that can be rebuilt.

### LLM Hot-Swap

The LiveKit Agents framework `AgentSession` exposes `session.llm` which can be replaced. If direct replacement is not supported, we store the new LLM config and create a new session on the next turn boundary. Research needed during implementation to confirm the exact API.

### Verbosity Hot-Swap

`AgentSession` likely supports `session.update_instructions()` or similar. The orchestrator agent's instructions string is rebuilt with the new verbosity directive appended.

### Agent Acknowledgment

When settings change, the agent sends a brief data channel message back to the frontend: `{ type: "settings_ack", model, verbosity }`. The frontend displays a transient toast or updates the settings panel indicator.

## Data Channel Message Schema

```json
// Frontend -> Agent
{
  "type": "settings_update",
  "model": "claude-haiku-4-5-20250514",
  "verbosity": 2
}

// Agent -> Frontend (acknowledgment)
{
  "type": "settings_ack",
  "model": "claude-haiku-4-5-20250514",
  "verbosity": 2
}
```

## Edge Cases

- **Message arrives during response**: Queue it; apply after current response completes
- **Invalid model/verbosity**: Ignore and log warning, send error ack
- **Multiple rapid changes**: Only the latest settings matter; debounce on frontend (300ms)
- **Disconnection**: Settings persist in localStorage, re-sent on reconnect via token API as before

## Non-Goals

- Changing STT/TTS providers mid-session
- Retroactive changes to past responses
