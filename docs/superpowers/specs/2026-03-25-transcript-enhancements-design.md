# Transcript Enhancements Design

**Date:** 2026-03-25
**Story:** #27 — Enhance transcript: group utterances and use local timestamps

## Problem

1. **Fragmented utterances** — Deepgram STT emits frequent final segments. Even small pauses mid-sentence produce separate transcript lines, making conversations hard to follow.
2. **Session-relative timestamps** — The current `formatElapsedTime(elapsedMs)` shows `HH:MM:SS` from session start. Users want local wall-clock time (e.g., "2:35 PM").

## Design

### 1. Utterance Grouping

**Approach:** After building the sorted `TranscriptEntry[]` array, run a grouping pass that merges consecutive entries from the same speaker when the time gap between them is below a configurable threshold.

**Algorithm:**
```
groupedTranscript = []
for each entry in sortedTranscript:
  if groupedTranscript is not empty
     AND entry.speaker == lastGroup.speaker
     AND (entry.timestamp - lastGroup.lastTimestamp) < GROUPING_WINDOW_MS:
    append entry.text to lastGroup.text (space-separated)
    update lastGroup.lastTimestamp = entry.timestamp
    merge entry.id into lastGroup.ids
  else:
    push new group from entry
```

**Constants:**
- `GROUPING_WINDOW_MS = 2000` (2 seconds, configurable)

**Data model change:**
```ts
interface GroupedTranscriptEntry {
  ids: string[];           // all original entry IDs merged
  speaker: "user" | "agent" | "user-text";
  text: string;            // concatenated texts
  timestamp: Date;         // first entry's timestamp (for display)
  lastTimestamp: Date;     // last entry's timestamp (for gap detection)
}
```

Gap detection uses `lastTimestamp` of the previous group and `timestamp` of the current group, preserving existing pause indicators.

### 2. Local Wall-Clock Timestamps

**Approach:** Replace `formatElapsedTime(elapsedMs)` with a new `formatLocalTime(date: Date)` function that uses `Intl.DateTimeFormat` or `Date.toLocaleTimeString()` with hour/minute/period.

**Format:** `h:mm AM/PM` (e.g., "2:35 PM") — uses the user's locale by default.

**Implementation:**
```ts
export function formatLocalTime(date: Date): string {
  return date.toLocaleTimeString([], {
    hour: "numeric",
    minute: "2-digit",
  });
}
```

This respects the browser locale automatically (12hr or 24hr).

### 3. Files Changed

| File | Change |
|------|--------|
| `frontend/src/lib/transcript-time.ts` | Add `formatLocalTime()`, add `groupTranscriptEntries()`, keep `detectGap()` and `getSessionStartTime()` |
| `frontend/src/app/page.tsx` | Use `groupTranscriptEntries()` on the transcript array, use `formatLocalTime()` instead of `formatElapsedTime()` |
| `frontend/src/lib/transcript-time.test.ts` | New file — unit tests for all functions |

### 4. What NOT to Change

- `formatElapsedTime` — keep it exported (may be used elsewhere or in future)
- `detectGap` — keep it, but feed it `lastTimestamp` from grouped entries
- `getSessionStartTime` — keep it (still needed for gap detection base)
- Settings panel files — another agent is working on those

## Risks

- **Grouping window too aggressive** — could merge distinct sentences. 2s is conservative; Deepgram typically emits finals within 300-500ms of each other for continuous speech.
- **Locale edge cases** — `toLocaleTimeString` behavior varies across runtimes; tested in jsdom via Vitest which uses the system locale.
