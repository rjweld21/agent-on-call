# Agent On Call — MVP Design Spec

> **Status:** Draft
> **Date:** 2026-03-21
> **Version:** v1

---

## 1. Overview

Agent On Call is a voice-first AI agent platform where a user joins a call and has natural conversations with an AI orchestrator. The orchestrator can spawn specialized sub-agents that join the call as visible participants, each handling different tasks concurrently. Sub-agents work independently and queue for user guidance when needed.

### Vision

- **Open-source core** — anyone can run Agent On Call locally with their own API keys
- **Future hosted product** — managed service with multi-tenancy, billing, and premium connectors (Zoom, Discord)
- **Multi-persona platform** — initially targets solo developers, extensible to team leads and non-technical professionals

### MVP Scope

The MVP delivers a working local experience: a user opens a browser, joins a LiveKit room, speaks to an AI orchestrator that can dispatch sub-agents visible in the participant list. Sub-agents that need guidance wait in a queue, and the orchestrator mentions them at natural conversation breaks.

---

## 2. Architecture

### 2.1 Voice Pipeline

The system uses a modular cascaded pipeline for voice interaction:

```
User speaks → Deepgram Flux (STT) → LLM (Claude/GPT) → Cartesia Sonic Turbo (TTS) → User hears response
```

**Component selection rationale:**

| Component | Choice | Why |
|-----------|--------|-----|
| STT | Deepgram Flux | Best accuracy (5.26% WER), sub-300ms latency, built-in turn detection, $0.0077/min |
| LLM | Claude / GPT-4o (configurable) | LLM-agnostic design — user chooses via config. No vendor lock-in |
| TTS | Cartesia Sonic Turbo | 40ms time-to-first-audio (fastest available), WebSocket streaming |
| Transport | LiveKit Agents Framework | Open-source, handles WebRTC/turn detection/interruption, existing Deepgram + Cartesia plugins |

**Estimated cost per minute:** ~$0.05-0.10 (STT + TTS + LLM tokens), vs $0.30/min for OpenAI Realtime API.

### 2.2 System Components

```
┌─────────────────────────────────────────────────┐
│                   User (Browser)                 │
│         Opens LiveKit room URL, speaks           │
└─────────────────────┬───────────────────────────┘
                      │ WebRTC Audio
┌─────────────────────▼───────────────────────────┐
│               LiveKit Server                     │
│     Room management, WebRTC, audio routing       │
│     (Docker local or LiveKit Cloud)              │
└──────┬──────────────────────────────┬───────────┘
       │ LiveKit SDK                  │ LiveKit SDK
┌──────▼──────────┐          ┌───────▼────────────┐
│  Orchestrator   │          │   Sub-Agent(s)      │
│  Agent          │ spawns → │   Named participants│
│                 │          │   in the room       │
│  • STT (Deepgram)│         │                     │
│  • LLM reasoning │         │   • Work on tasks   │
│  • TTS (Cartesia)│         │   • Report results  │
│  • Sub-agent mgmt│         │   • Queue for input │
│  • Guidance queue│         │   • Leave when done  │
└─────────────────┘          └─────────────────────┘
```

### 2.3 Orchestrator Agent

The orchestrator is a single LiveKit Agent (Python) with these responsibilities:

**Voice interface:**
- Listens to user speech via Deepgram Flux STT
- Processes with LLM (Claude/GPT) for reasoning and response generation
- Speaks back via Cartesia Sonic Turbo TTS
- Handles turn detection and interruption (via LiveKit Agents framework)

**Sub-agent coordination:**
- Dispatches sub-agents based on user requests
- Assigns descriptive names (e.g., "Research - DB Selection")
- Monitors sub-agent status (working, waiting, done)
- Maintains a guidance queue for sub-agents needing input
- Mentions waiting sub-agents at natural conversation breaks
- Relays sub-agent results back to the user verbally
- Announces when sub-agents join or leave

**Design for future split:**
The orchestrator's voice interface and coordination logic should communicate through a well-defined internal interface (message passing, not shared state). This enables a future enhancement to split into separate Communicator and Coordinator agents without rewriting the core logic.

### 2.4 Sub-Agent Model

Sub-agents are lightweight LiveKit Agents that join the room as named participants:

- **Creation:** Orchestrator spawns a new agent process, which joins the LiveKit room with a descriptive display name
- **Visibility:** Appears in the participant list so the user can see active agents
- **Communication:** Reports status and results to the orchestrator via LiveKit data channels or an internal message bus
- **No voice:** Sub-agents do not listen to or produce audio in MVP. The orchestrator relays all communication
- **Lifecycle:** Joins room → works on task → reports result (or queues for guidance) → leaves room when done

**Sub-agent states:**
- `working` — actively processing the task
- `waiting_for_input` — blocked, needs user guidance (enters guidance queue)
- `done` — completed, result available, leaves room

### 2.5 Guidance Queue

When a sub-agent needs user input, it enters the guidance queue:

1. Sub-agent sends a guidance request to the orchestrator (what it needs, why it's blocked)
2. Orchestrator adds it to an in-memory queue (list of pending requests)
3. At natural conversation breaks (pause in speech, topic transition), the orchestrator mentions: "By the way, [Agent Name] has a question about [topic] — want to address that now or later?"
4. User responds → orchestrator relays the answer to the sub-agent
5. Sub-agent resumes work

**MVP implementation:** In-memory Python data structure (list/dict). No Redis required.

**Future enhancement:** Persistent queue with a chat-based status panel showing all agents and their states.

---

## 3. Call Platform

### 3.1 MVP: LiveKit Rooms

Users connect directly to a LiveKit room via browser. No third-party call platform integration needed.

**User flow:**
1. Start the agent system locally (`docker-compose up` or `python agent.py dev`)
2. Open the provided localhost URL in a browser
3. Grant microphone access
4. Start talking — the orchestrator responds

**Why LiveKit rooms for MVP:**
- Eliminates third-party API integration complexity
- LiveKit is the transport layer regardless — agents always live in a LiveKit room
- Adding Zoom/Discord later means adding "front doors" (audio bridges) to the same room
- Agent code doesn't change when adding new platforms

### 3.2 Future Platform Connectors

| Platform | How It Connects | Repo |
|----------|----------------|------|
| LiveKit (MVP) | Direct browser join | Public (open-source) |
| Discord | Discord bot captures audio → bridges into LiveKit room | TBD (public or private) |
| Zoom | Zoom Meeting SDK bot → bridges audio into LiveKit room | Private (cloud product) |

---

## 4. Infrastructure

### 4.1 Local Development Stack

```yaml
# What runs locally for development
services:
  livekit:     # LiveKit server (WebRTC, room management)
  agent:       # Python agent worker (orchestrator + sub-agents)
  redis:       # Optional — sub-agent state (can use in-memory for MVP)
```

**Prerequisites:**
- Python 3.11+
- Docker Desktop
- API keys: Deepgram, Cartesia, Anthropic/OpenAI, LiveKit

**Setup:**
1. Clone repo
2. Copy `.env.example` to `.env`, fill in API keys
3. `docker-compose up`
4. Open browser to localhost URL

### 4.2 Configuration

All deployment differences are handled via environment variables:

| Variable | Local | Production |
|----------|-------|-----------|
| `LIVEKIT_URL` | `ws://localhost:7880` | `wss://cloud.livekit.io` or self-hosted URL |
| `LIVEKIT_API_KEY` | Local dev key | Cloud or self-hosted key |
| `LIVEKIT_API_SECRET` | Local dev secret | Cloud or self-hosted secret |
| `DEEPGRAM_API_KEY` | User's key | Managed by platform |
| `CARTESIA_API_KEY` | User's key | Managed by platform |
| `LLM_API_KEY` | User's key | Managed by platform |
| `LLM_PROVIDER` | `anthropic` or `openai` | Configurable |

### 4.3 Production Path

The same agent codebase deploys to production with only config changes:

- **LiveKit Cloud** or self-hosted LiveKit server
- **Containerized agent workers** (Docker)
- **Managed API keys** via the cloud platform's key vault
- **CI/CD:** GitHub Actions for testing + deployment

---

## 5. Distribution & Licensing

### 5.1 Open-Core Model

| Repo | Visibility | Contents |
|------|-----------|----------|
| `agent-on-call` | **Public** (AGPL) | Core agent framework, orchestrator, sub-agent system, guidance queue, docker-compose for local, CLI |
| `agent-on-call-cloud` | **Private** (Proprietary) | Multi-tenant platform, auth/billing, managed API key vault, Zoom/Discord connectors, IaC, CI/CD deployment |

### 5.2 Licensing: AGPL v3

- Anyone can use, modify, and self-host Agent On Call
- If they modify it and run it as a service, they must open-source their modifications
- The private cloud repo is a separate codebase that imports the AGPL package — it remains proprietary
- Can be relicensed later if needed

### 5.3 CI/CD

**Public repo (`agent-on-call`):**
- GitHub Actions: lint (flake8, black), type check (mypy), unit tests (pytest), coverage
- Publish Python package to PyPI on release

**Private repo (`agent-on-call-cloud`) — future:**
- Pull latest core package
- Build containers
- Deploy infrastructure (Terraform/CDK)
- Integration tests against staging

---

## 6. Future Enhancements (Post-MVP)

Noted during brainstorming and initial testing, deferred from MVP scope:

### 6.1 Agent Tooling (High Priority)

The orchestrator and sub-agents need access to real tools to be useful beyond conversation:

- **Shell/command execution** — Run terminal commands (git clone, npm install, pytest, etc.)
- **File system access** — Read, write, and edit files in a workspace directory
- **Git operations** — Clone repos, create branches, commit, push
- **Web search/fetch** — Research topics, read documentation
- **Code analysis** — Read and understand codebases

**Implementation approach:** LiveKit Agents supports `function_tool` decorators on the Agent class. Each tool is exposed to the LLM as a callable function. Tools should be sandboxed to a workspace directory per session.

**Architecture consideration:** Tools run in the agent's Docker container. For security, each session should have an isolated workspace (volume mount or temporary directory). Sub-agents inherit a subset of tools relevant to their task.

### 6.2 Session Context & Persistence (High Priority)

The agent needs to maintain state across conversations and start from where it left off:

- **Startup context** — Load project context, previous conversation summary, and active tasks when a session begins
- **Session persistence** — Save conversation history, decisions made, and work-in-progress to disk/database
- **Project profiles** — User defines projects with their repo URL, tech stack, and preferences. Agent loads the right context when a project is selected.
- **Multi-project support** — Switch between projects mid-call ("Switch to the agent-on-call project")
- **Resume capability** — "Continue where we left off" loads the last session's state

**Implementation approach:** Store session state as JSON/YAML files in a `sessions/` directory. On session start, load the most recent session for the selected project. The orchestrator's system prompt is dynamically built from project context + conversation history.

### 6.3 Transcript Display (Bug Fix — Near Term)

The frontend transcript panel exists but doesn't receive transcription events from LiveKit. Need to:
- Hook into LiveKit's `TranscriptionReceived` room event (not the voice assistant hook)
- Display both user speech (from STT) and agent speech (from TTS) in real-time
- This is a frontend wiring issue, not a backend issue — STT is working server-side

### 6.4 Platform & Architecture

1. **Communicator/Coordinator split** — Separate the orchestrator's voice interface from sub-agent coordination into two agents
2. **Chat-based status panel** — Persistent sidebar showing all agent statuses, waiting items, and history
3. **Direct sub-agent conversation** — User can address sub-agents by name to talk directly
4. **Zoom connector** — Zoom Meeting SDK bot bridges audio to LiveKit room
5. **Discord connector** — Discord bot bridges audio to LiveKit room
6. **OpenRouter support** — Single API key for 100+ LLM models via OpenAI-compatible endpoint
7. **Configurable STT/TTS providers** — Swap Deepgram/Cartesia for alternatives via env var

### 6.5 Workspace Container Architecture

Each project lives in its own Docker container with a persistent volume. The orchestrator manages workspace containers via Docker socket (sibling containers, not nested).

**Composable base images:** Agent tools layer is a separate Dockerfile stage that copies onto any base image. Users choose a profile or provide their own:
- `dev` (default) — python:3.11-slim + git, node, npm, gcc
- `minimal` — alpine:3.19 + curl, jq
- `data` — python:3.11-slim + pandas, numpy, matplotlib
- `custom` — user's own Dockerfile

Implementation: `ARG BASE_IMAGE=python:3.11-slim` in Dockerfile, build with `--build-arg`.

**Text input box:** Frontend includes a text input alongside voice. Sent via LiveKit data channel. Agent receives both voice (STT) and text input. Essential for URLs, code snippets, and anything impractical to spell out verbally.

### 6.6 Security Considerations (Managed Cloud Only)

For the local open-source version, agent infrastructure awareness is a feature — the user owns the machine.

For the managed cloud product, the following security workstream is required before launch:

| Vector | Mitigation |
|--------|-----------|
| Docker socket exposure | Workspace containers never get socket access. Only orchestrator. |
| API key leakage | Keys in orchestrator only. Workspaces get scoped proxy access. |
| Infrastructure probing | System prompt restrictions. Workspace agents get no infra context. |
| Network scanning | Isolated network per workspace. Outbound via allow-list proxy. |
| Filesystem escape | Tools restricted to /workspace/. Read-only root FS. No /proc, /sys. |
| Cross-tenant access | Isolated volumes per user. Container namespace isolation. |
| Resource exhaustion | CPU/memory limits per container. Auto-terminate on idle timeout. |

---

## 7. Testing Strategy

### Unit Tests
- Orchestrator logic (sub-agent dispatch, guidance queue, state management)
- Sub-agent lifecycle (creation, status transitions, cleanup)
- Message routing between orchestrator and sub-agents
- Configuration loading and validation

### Integration Tests
- Voice pipeline end-to-end (mocked STT/TTS APIs)
- LiveKit room participant management
- Sub-agent join/leave lifecycle
- Guidance queue flow (request → queue → mention → relay → resume)

### E2E Tests
- Full voice conversation with mocked audio input
- Sub-agent dispatch and completion via Playwright (browser-based LiveKit room)

### Coverage Targets
| Layer | Target |
|-------|--------|
| Core orchestrator logic | >= 90% |
| Sub-agent lifecycle | >= 90% |
| API/config handling | >= 85% |
| Voice pipeline integration | >= 80% |

---

## 8. Success Criteria (MVP)

The MVP is complete when:

1. User can open a browser, join a LiveKit room, and have a natural voice conversation with the orchestrator
2. User can ask the orchestrator to perform a task, and a named sub-agent appears in the participant list
3. Sub-agent works independently and the orchestrator announces the result when complete
4. If a sub-agent needs guidance, the orchestrator mentions it at a natural break in conversation
5. User can respond to the guidance request and the sub-agent resumes
6. The entire system runs locally via `docker-compose up` with user-provided API keys
7. Setup takes less than 10 minutes for a developer with Docker and API keys ready
