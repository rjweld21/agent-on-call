# Turn-Taking Tuning — Design Spec

**Date:** 2026-03-25
**Story:** #29 — Tune turn-taking: smarter pause detection

## Overview

Tune VAD endpointing delay and turn detector sensitivity to reduce premature agent responses when users pause mid-thought. Uses configuration dataclasses for VAD and turn-taking parameters.

## Tuning Decisions

### VAD Configuration (Silero)
| Parameter | Default | Tuned | Rationale |
|-----------|---------|-------|-----------|
| min_silence_duration | 0.55s | 0.8s | Allows natural thinking pauses (0.5-1.0s) without triggering |
| activation_threshold | 0.5 | 0.55 | Reduces false triggers from background noise |

### Turn-Taking Configuration (AgentSession)
| Parameter | Default | Tuned | Rationale |
|-----------|---------|-------|-----------|
| min_endpointing_delay | 0s | 0.6s | Minimum silence before considering turn complete |
| max_endpointing_delay | - | 3.0s | Maximum wait; responds after 3s silence regardless |
| min_interruption_duration | 0s | 0.5s | Prevents accidental interrupts (coughs, etc.) |
| min_interruption_words | 0 | 2 | Requires substantive speech to interrupt |

### Architecture
- `turn_taking.py` module with frozen dataclasses: `VADConfig` and `TurnTakingConfig`
- Default instances: `DEFAULT_VAD_CONFIG` and `DEFAULT_TURN_TAKING_CONFIG`
- Applied in `main.py` during session creation
- Future: configurable via env vars or settings panel

## File Structure
```
src/agent_on_call/turn_taking.py    — Configuration dataclasses
src/agent_on_call/main.py           — Apply configs to VAD and AgentSession
tests/test_turn_taking.py           — 6 unit tests
```
