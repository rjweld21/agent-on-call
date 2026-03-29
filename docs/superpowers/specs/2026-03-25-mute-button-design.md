# Mute Button Design

**Date:** 2026-03-25
**Story:** #35 — Add mute/unmute button for user microphone

## Problem

Users have no in-app way to mute their microphone during a call. They must rely on browser or OS-level controls, which is inconvenient and inconsistent.

## Constraints

- LiveKit Components React v2.9 — use framework track controls
- Must integrate with existing call controls area in page.tsx
- Agent should stop processing speech when user is muted
- Visual state must be immediately obvious (icon + color)

## Approach

### MuteButton Component

Create a `MuteButton` component at `frontend/src/app/components/MuteButton.tsx` that:

1. Uses `useLocalParticipant()` from `@livekit/components-react` to get the local participant
2. Calls `localParticipant.setMicrophoneEnabled(false/true)` to toggle mute
3. Reads `isMicrophoneEnabled` from the local participant to show current state
4. Displays a microphone icon (muted: red slash-mic, unmuted: green mic)

### Keyboard Shortcut

- **M key**: Toggle mute/unmute (only when not typing in text input)
- Event listener on document, checks `e.target` is not an input/textarea before acting

### Visual Design

- Circular button matching existing UI style (dark slate background, colored border)
- Unmuted: green border, white mic icon
- Muted: red border, red mic-slash icon, slight red background tint
- Tooltip showing current state and keyboard shortcut hint

### Placement

In `page.tsx`, the MuteButton goes in the call controls area, between the MicMonitor and the DisconnectButton. It should be visually grouped with call actions.

### Agent Awareness

When the user mutes via LiveKit's `setMicrophoneEnabled(false)`, the audio track is disabled at the WebRTC level. The agent's STT will simply receive no audio — no explicit notification needed. The agent naturally stops hearing speech and waits.

## Component API

```tsx
// No props needed — reads from LiveKit context
<MuteButton />
```

## Accessibility

- `aria-label`: "Mute microphone" / "Unmute microphone"
- `role="button"`
- Keyboard accessible (Enter/Space to toggle, M as global shortcut)
- Focus ring visible

## Edge Cases

- **Mute during agent response**: Agent continues speaking; user just can't be heard
- **Mute while speaking**: Current STT segment may produce partial transcription; this is acceptable
- **Keyboard shortcut while typing**: Ignored when focus is on text input
