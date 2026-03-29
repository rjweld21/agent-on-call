# Settings Panel Implementation Plan

**Date:** 2026-03-25
**Story:** #30 — Add settings screen with side navigation panel
**Branch:** feat/settings-panel

## Tasks

### Task 1: Settings Context and Hook

**Files:** `frontend/src/lib/settings-context.tsx`, `frontend/src/lib/settings-context.test.tsx`

1. Write tests for:
   - `useSettings` returns default settings on first load
   - `updateSetting` persists to localStorage
   - Settings loaded from localStorage on mount
   - Invalid localStorage data falls back to defaults
2. Implement `SettingsProvider` with React context + useReducer
3. Implement `useSettings` hook
4. Settings shape: `Record<string, Record<string, unknown>>` with typed defaults
5. localStorage key: `aoc-settings`

### Task 2: SettingsPanel Component

**Files:** `frontend/src/app/components/SettingsPanel.tsx`, `frontend/src/app/components/SettingsPanel.test.tsx`

1. Write tests for:
   - Panel renders when `isOpen=true`, hidden when `isOpen=false`
   - Close button calls `onClose`
   - Clicking backdrop calls `onClose`
   - Escape key calls `onClose`
   - Sections render with titles
2. Implement SettingsPanel component:
   - Props: `isOpen: boolean`, `onClose: () => void`
   - Backdrop overlay with click handler
   - Panel container with slide animation (CSS transform)
   - Header with title and close (X) button
   - Section list with collapsible sections
   - Responsive width: 360px desktop, 90vw max

### Task 3: Integrate into Room UI

**File:** `frontend/src/app/page.tsx`

1. Add gear icon button to AgentInterface header (next to "Agent On Call" title)
2. Add state: `const [settingsOpen, setSettingsOpen] = useState(false)`
3. Render `<SettingsPanel isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />`
4. Wrap the app with `<SettingsProvider>` in layout or page
5. Verify panel does not unmount LiveKitRoom or interrupt audio

### Task 4: E2E Test

**File:** `frontend/e2e/settings-panel.spec.ts`

1. Navigate to the home page (pre-connection state)
2. Note: E2E cannot easily test inside LiveKitRoom (needs token), so test the settings button visibility and panel behavior using a mock or testing the component in isolation
3. Alternative: Add a data-testid to the settings button, write Playwright test that:
   - Loads the page
   - Connects (if possible) or verifies settings button is in DOM
   - Clicks settings, verifies panel appears
   - Closes panel via close button, escape, backdrop

## Existing Code to Reuse

- `frontend/src/app/page.tsx` — AgentInterface component (modify)
- `frontend/vitest.config.ts` — test configuration (no changes needed)
- `frontend/src/test-setup.ts` — test setup (no changes needed)
- Pattern from `transcript-time.test.ts` for test structure

## Test Strategy

- **Unit tests:** Settings context (localStorage interaction), Panel component (open/close/escape/backdrop)
- **E2E test:** Settings panel interaction on the page (Playwright)
- Target: 80%+ coverage on new code
