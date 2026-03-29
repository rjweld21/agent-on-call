# Mute Button Implementation Plan

**Date:** 2026-03-25
**Story:** #35 — Add mute/unmute button for user microphone
**Branch:** `feat/mute-button`

## Task Breakdown

### Task 1: MuteButton component

**Test first:** `frontend/src/app/components/MuteButton.test.tsx`
- Test renders with unmuted state by default
- Test clicking toggles mute state
- Test shows correct icon/color for muted vs unmuted
- Test aria-label changes based on state
- Test calls `localParticipant.setMicrophoneEnabled` with correct value

**Implementation:**
- Create `frontend/src/app/components/MuteButton.tsx`
- Use `useLocalParticipant()` from `@livekit/components-react`
- Read `isMicrophoneEnabled` for current state
- On click: `localParticipant.setMicrophoneEnabled(!isMicrophoneEnabled)`
- Render circular button with mic/mic-slash icon (Unicode or inline SVG)
- Style: green border when unmuted, red border + red tint when muted

**Files:** `frontend/src/app/components/MuteButton.tsx`, `frontend/src/app/components/MuteButton.test.tsx`

### Task 2: Keyboard shortcut

**Test first:** extend `MuteButton.test.tsx`
- Test M key toggles mute when no input focused
- Test M key does NOT toggle when typing in text input
- Test shortcut works regardless of case

**Implementation:**
- In `MuteButton.tsx`, add `useEffect` with document keydown listener
- Check `e.key === 'm' || e.key === 'M'`
- Check `document.activeElement?.tagName` is not INPUT or TEXTAREA
- Call toggle function

**Files:** `frontend/src/app/components/MuteButton.tsx`

### Task 3: Integrate into page.tsx

**Test first:** `frontend/src/app/test/page.test.tsx` (extend existing)
- Test MuteButton is rendered in the call interface
- Test MuteButton appears between MicMonitor and DisconnectButton

**Implementation:**
- Import `MuteButton` in `page.tsx`
- Add `<MuteButton />` in `AgentInterface` component between MicMonitor and DisconnectButton
- Add a wrapper div for call controls grouping if needed

**Files:** `frontend/src/app/page.tsx`

### Task 4: E2E test

**Test first:** `frontend/e2e/mute-button.spec.ts`
- Navigate to app, start call (or verify mute button is present in call UI)
- Click mute button, verify visual state changes
- Click again to unmute, verify state reverts
- Test keyboard shortcut M

**Files:** `frontend/e2e/mute-button.spec.ts`

## Implementation Order

1. Task 1 (MuteButton component + tests)
2. Task 2 (keyboard shortcut, extends Task 1)
3. Task 3 (integrate into page.tsx)
4. Task 4 (E2E test)

## Existing Code to Reuse

- `useLocalParticipant()` — already imported in page.tsx, used by MicMonitor
- Button styling patterns — match DisconnectButton and settings button styles
- `@livekit/components-react` — already a dependency

## Risk

- Low risk. LiveKit's `setMicrophoneEnabled` is a well-documented, stable API. The component is self-contained with no backend changes needed.
