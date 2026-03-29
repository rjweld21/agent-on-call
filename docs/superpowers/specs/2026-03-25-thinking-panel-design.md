# Agent Thinking Panel — Design Spec

**Date:** 2026-03-25
**Story:** #26 — Add agent thinking and activity panel to frontend

## Overview

Add a collapsible panel to the AgentInterface that shows agent activity in real-time: thinking states, command execution, tool calls, and results. Provides visibility into what the agent is doing during processing.

## Design Decisions

### Component Architecture
- `ThinkingPanel` — standalone component accepting `activities` and `isAgentWorking` props
- Activity items have types: thinking (italic/gray), executing (monospace/green), tool_call (amber), result (blue)
- Collapsible with toggle button, auto-scrolls to latest activity
- Empty state message when no activities

### Activity Tracking
- Agent state transitions tracked via `useVoiceAssistant` state
- "thinking" state -> adds thinking activity
- "speaking" after "thinking" -> adds result activity
- Future: tool call events from LiveKit data channel will add executing/tool_call items

### Position
- Between MicMonitor and Participants sections in the main interface
- Full width (max 500px), matches existing layout

## File Structure
```
frontend/src/app/components/ThinkingPanel.tsx      — Component with types
frontend/src/app/components/ThinkingPanel.test.tsx  — 10 unit tests
frontend/src/app/page.tsx                          — Integration with AgentInterface
```
