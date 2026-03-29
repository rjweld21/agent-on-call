# Settings Panel Design Spec

**Date:** 2026-03-25
**Story:** #30 — Add settings screen with side navigation panel

## Overview

Add a slide-out settings panel to the room UI that overlays from the right side without interrupting the active voice session. The panel provides a container for future settings (model selector, verbosity, turn-taking) and persists state via localStorage.

## Design Decisions

### Component Architecture

1. **SettingsPanel** — slide-out drawer component (pure presentation + open/close logic)
2. **SettingsProvider** — React context that holds settings state, reads/writes localStorage
3. **useSettings** — hook to access settings from any component
4. **Settings button** — gear icon added to the AgentInterface header

### Why React Context over Zustand

The story mentions zustand as an option, but the settings state is simple key-value pairs with no complex derived state. React Context + useReducer keeps dependencies minimal and is sufficient for this use case. Zustand can be introduced later if settings grow complex.

### Panel Behavior

- Slides in from the right edge, 360px wide (max 90vw on narrow screens)
- Semi-transparent backdrop overlay (click to close)
- Close on Escape key press
- Close button (X) in panel header
- CSS transform animation for smooth slide (translateX)
- Panel renders as a portal or sibling to room content — does NOT unmount the room or pause audio
- z-index above room content but below any modals

### Settings Persistence

- All settings stored in localStorage under key `aoc-settings`
- JSON object: `{ [category]: { [key]: value } }`
- Loaded once on provider mount, written on every change
- Default values defined in a constants file

### Section Layout

The panel has a vertical list of collapsible sections. Each section has:
- Section title
- Optional description
- Content area where individual setting controls will be added by future stories

Initial sections (empty, placeholder):
- **General** — placeholder for general preferences
- **Model** — placeholder for model selection
- **Voice** — placeholder for verbosity and turn-taking controls

### Accessibility

- Focus trap when panel is open (Tab cycles within panel)
- Escape closes panel
- aria-label on panel, close button
- Settings button has aria-label

## File Structure

```
frontend/src/lib/settings-context.tsx    — SettingsProvider, useSettings hook
frontend/src/lib/settings-context.test.tsx — unit tests for context/hook
frontend/src/app/components/SettingsPanel.tsx — panel UI component
frontend/src/app/components/SettingsPanel.test.tsx — unit tests for panel
```

## Out of Scope

- Individual setting controls (separate stories)
- Server-side persistence
- Mobile-specific layout
- Focus trap implementation (can be enhanced later)
