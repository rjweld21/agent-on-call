# Transcript Enhancements Implementation Plan

**Date:** 2026-03-25
**Story:** #27 — Enhance transcript: group utterances and use local timestamps

## Tasks

### Task 1: Add `formatLocalTime()` to transcript-time.ts (RED-GREEN-REFACTOR)

**File:** `frontend/src/lib/transcript-time.ts`

- **RED:** Write tests in `frontend/src/lib/transcript-time.test.ts`:
  - `formatLocalTime` returns a string containing hour and minute
  - `formatLocalTime` handles midnight, noon, PM times
- **GREEN:** Implement `formatLocalTime(date: Date): string` using `toLocaleTimeString`
- **REFACTOR:** Clean up

### Task 2: Add `groupTranscriptEntries()` to transcript-time.ts (RED-GREEN-REFACTOR)

**File:** `frontend/src/lib/transcript-time.ts`

- **RED:** Write tests:
  - Empty array returns empty array
  - Single entry returns one group
  - Two entries from same speaker within 2s are merged
  - Two entries from same speaker beyond 2s are separate
  - Entries from different speakers are never merged even if within window
  - Merged text is space-separated
  - Group preserves first timestamp and tracks last timestamp
  - Three rapid entries from same speaker all merge into one
- **GREEN:** Implement `groupTranscriptEntries()` per spec algorithm
- **REFACTOR:** Extract `GROUPING_WINDOW_MS` as exported constant

### Task 3: Update page.tsx to use grouped transcript and local timestamps

**File:** `frontend/src/app/page.tsx`

- Import `formatLocalTime` and `groupTranscriptEntries`
- Apply `groupTranscriptEntries()` to the sorted transcript array
- Replace `formatElapsedTime(elapsedMs)` with `formatLocalTime(entry.timestamp)`
- Update gap detection to use `lastTimestamp` from grouped entries
- Remove unused `getSessionStartTime` call (no longer needed for elapsed calc, but keep for gap detection compatibility)
- Use group `ids` joined for React key instead of single `entry.id`

### Task 4: Run tests and verify

- Run `cd frontend && npx vitest run`
- Verify all new tests pass
- Verify no existing tests broken (there are none currently, but check)
- Run `npx tsc --noEmit` to verify types
