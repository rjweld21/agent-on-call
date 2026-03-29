# Verbosity Slider — Design Spec

**Date:** 2026-03-25
**Story:** #31 — Add verbosity slider (1-5) to settings panel

## Overview

Add a 1-5 verbosity slider to the Voice section of the settings panel. Each level maps to a distinct system prompt fragment that controls how concise or detailed the agent's responses are.

## Design Decisions

### Slider Component
- HTML range input with min=1, max=5, step=1 (snaps to integers)
- Labels: "Concise" at left (1), "Wordy" at right (5)
- Current level displayed as "N — LevelName"
- Tooltip (?) explaining the scale

### Verbosity Levels
| Level | Name | Behavior |
|-------|------|----------|
| 1 | Concise | Bare minimum, may skip details |
| 2 | Brief | Short but complete |
| 3 | Balanced | Natural conversational (default) |
| 4 | Detailed | Step-by-step explanations |
| 5 | Verbose | Full detail, tutorial-like |

### How Verbosity Reaches the Agent
- Stored in settings context under `voice.verbosity`
- Sent to token API as `?verbosity=N` query param
- Embedded in participant metadata: `{ model, verbosity }`
- Backend reads from metadata, appends verbosity directive to orchestrator instructions

### Persistence
- localStorage via existing settings context
- Default is 3 (Balanced)

## File Structure
```
frontend/src/app/components/VerbositySlider.tsx      — Component + prompt definitions
frontend/src/app/components/VerbositySlider.test.tsx  — Unit tests
frontend/src/app/components/SettingsPanel.tsx         — Integrate into Voice section
frontend/src/app/api/token/route.ts                  — Accept verbosity param
frontend/src/app/page.tsx                            — Pass verbosity to token API
src/agent_on_call/main.py                           — Read verbosity, append to instructions
```
