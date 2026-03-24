# Agent On Call — Running Backlog

> **Last Updated:** 2026-03-24
> **Status:** MVP shipped to master. Open source at github.com/rjweld21/agent-on-call

---

## Pre-MVP (DONE)

All completed and merged to master.

- [x] Project scaffolding & CI/CD (M1)
- [x] Config module & message schemas (M2)
- [x] Docker + LiveKit server (M3)
- [x] Frontend browser UI (M4)
- [x] Voice pipeline — Deepgram STT → Claude LLM → Cartesia TTS (M5)
- [x] Workspace containers + agent tools — run_command, read/write files (M6a)
- [x] Transcript display with timestamps
- [x] Text input box (paste URLs, type messages)
- [x] Mic monitor (audio level meter)
- [x] Orchestrator static name ("Orchestrator")
- [x] Workspace environment awareness in system prompt
- [x] Audio test page (/test)
- [x] LLM provider flexibility (Anthropic / OpenAI via env var)
- [x] Comprehensive README with quickstart
- [x] AGPL v3 license
- [x] 20 unit tests passing

---

## Post-MVP (Open Source Enhancements)

Items that improve the open-source local experience. No cloud infrastructure required.

### High Priority

- [ ] **Sub-agent dispatch (M6b)** — Orchestrator spawns named LiveKit agents for concurrent tasks. RPC communication, guidance queue integration. Sub-agents use Model B (no audio, orchestrator relays via RPC).
- [ ] **Session persistence & resume** — Save conversation history + context to `.aoc/` in workspace volume. On resume, load `context-summary.md` into system prompt. "Continue where we left off" works.
- [ ] **Audio echo cancellation** — Agent TTS picked up by user mic causes STT confusion. Explore: LiveKit AEC, noise-cancellation plugin, Silero VAD tuning, browser echoCancellation constraint. Recommend headphones in docs as interim fix.
- [ ] **Web search/fetch tools** — Agent can research topics, read documentation, fetch URLs.

### Medium Priority

- [ ] **Terminal output panel (UI)** — Separate panel showing commands the agent runs and their output. Distinct from transcript ("what agent is doing" vs "what we're talking about"). Real-time streaming for long commands.
- [ ] **Transcript logging to file** — Save full transcript as JSON with timestamps to `.aoc/transcripts/YYYY-MM-DD-HHMMSS.json`. Track pause duration between entries.
- [ ] **Workspace selector UI** — Frontend dropdown to switch between projects or create new ones. API endpoint for listing/creating/switching workspaces.
- [ ] **Sub-agent UX indicators** — Task-based naming (e.g., "Research - DB Selection"). Activity indicators: green (working), yellow (needs input), gray (done). Highlight on communication. Notification badges for pending guidance.
- [ ] **OpenRouter support** — Single API key for 100+ LLM models via OpenAI-compatible endpoint. Set `LLM_PROVIDER=openrouter` in env.
- [ ] **Configurable STT/TTS providers** — `STT_PROVIDER` and `TTS_PROVIDER` env vars to swap Deepgram/Cartesia for AssemblyAI, ElevenLabs, etc.
- [ ] **Composable workspace profiles** — Ship prebuilt images: dev (Python+Node+Git), minimal (Alpine), data (pandas/numpy). User can provide custom Dockerfile.

### Low Priority

- [ ] **Sub-agent communication visibility** — Separate tab/panel showing orchestrator ↔ sub-agent messages. Expandable per-agent view with task, status, full message history.
- [ ] **Communicator/Coordinator split** — Separate orchestrator's voice interface from sub-agent coordination into two agents. Designed for but deferred.
- [ ] **Direct sub-agent conversation** — User addresses sub-agents by name to talk directly instead of always going through orchestrator.
- [ ] **Chat-based status panel** — Persistent sidebar showing all agent statuses, waiting items, and history.
- [ ] **Hybrid listening model** — Single STT stream fanned out as text to N listening sub-agents. Only added cost is LLM evaluation per agent. User toggle: "Allow agents to listen in" vs "Agents work independently."
- [ ] **Discord connector** — Discord bot captures audio → bridges into LiveKit room. Evaluate for public or private repo.
- [ ] **Multi-project switching mid-call** — "Switch to the agent-on-call project" swaps workspace context.

---

## Post-Open Source / Managed Product

Items specific to the hosted cloud product (private `agent-on-call-cloud` repo). Create this repo when MVP is stable and community feedback is gathered.

### Infrastructure & Security

- [ ] **Private repo creation** — `agent-on-call-cloud` (proprietary). Imports core package via `pip install agent-on-call`.
- [ ] **Multi-tenant architecture** — User accounts, workspace isolation per tenant, shared infrastructure.
- [ ] **Auth & billing** — OAuth login, subscription tiers, usage-based billing.
- [ ] **Managed API key vault** — Users don't manage STT/TTS/LLM keys. Platform handles keys and proxies requests.
- [ ] **IaC (Terraform/CDK)** — LiveKit Cloud or self-hosted, containerized agent workers, auto-scaling.
- [ ] **CI/CD deployment pipeline** — Pull latest core package, build containers, deploy to staging/prod, integration tests.

### Security Workstream (Required Before Cloud Launch)

- [ ] **Docker socket isolation** — Workspace containers never get socket access. Only orchestrator.
- [ ] **API key proxying** — Keys stay in orchestrator. Workspaces get scoped proxy access, not raw keys.
- [ ] **System prompt restrictions** — Workspace agents get no infrastructure context. Can't reveal how they're built.
- [ ] **Network isolation** — Each workspace on isolated network. Outbound only via allow-list proxy.
- [ ] **Filesystem sandboxing** — Tools restricted to /workspace/. Read-only root FS. No /proc, /sys, host mounts.
- [ ] **Cross-tenant isolation** — Isolated volumes per user. Container namespace isolation.
- [ ] **Resource limits** — CPU/memory limits per workspace container. Auto-terminate on idle timeout.
- [ ] **Penetration testing** — Full security audit before public launch.

### Monitoring & Operations

- [ ] **Container metrics dashboard** — CPU, memory consumption per workspace container.
- [ ] **Volume usage tracking** — Storage consumed per workspace volume, growth over time.
- [ ] **User-facing resource dashboard** — Show users their consumption.
- [ ] **Threshold alerts** — Notify users at 80% of allocated resources.
- [ ] **Scale recommendations** — Suggest tier upgrades based on usage patterns.
- [ ] **Billing integration** — Resource usage feeds into per-user billing.

### Agent Quality & Experience (Managed Product Differentiator)

- [ ] **Refined agent personality** — Less wordy, more direct responses. Tuned system prompts for production quality vs open-source default.
- [ ] **Response quality tuning** — A/B test different system prompts, temperature settings, and instruction styles for better advice quality.
- [ ] **Context management** — Smarter context window usage. Summarize long conversations. Prioritize recent and relevant information.
- [ ] **Domain-specific profiles** — Pre-tuned agent personalities for software dev, data analysis, research, writing. Managed product ships with refined profiles.
- [ ] **Conversation guardrails** — Prevent agent from going off-topic, making up capabilities, or giving harmful advice. More important in managed multi-user environment.
- [ ] **Voice quality options** — Multiple Cartesia voices to choose from. Custom voice cloning for enterprise.
- [ ] **Usage analytics** — Track conversation quality metrics (user satisfaction, task completion rate, error rate). Use data to improve prompts.

### Platform Connectors (Premium Features)

- [ ] **Zoom connector** — Zoom Meeting SDK bot bridges audio to LiveKit room. Private repo only.
- [ ] **Google Meet connector** — If API access improves.
- [ ] **Slack integration** — Agent available in Slack channels for text-based interaction.
- [ ] **Calendar integration** — Agent joins scheduled meetings automatically.

---

## Key Architectural Decisions (Reference)

| Decision | Rationale |
|----------|-----------|
| Container = Workspace | Each project gets isolated Docker container + persistent volume. Stop = pause. Start = resume. Delete = clean. |
| Model B for sub-agents (MVP) | Sub-agents communicate via RPC only, no audio. Orchestrator relays. Cost stays 1x STT. |
| Hybrid listening (future) | Single STT → fan out text to N agents. User toggle for cost vs responsiveness. |
| Composable base images | `ARG BASE_IMAGE` in Dockerfile. Users pick profile or provide own. |
| Docker socket for orchestrator only | Manages sibling containers. Workspaces never get socket. |
| AGPL license | OSS users contribute back. Cloud repo is separate and proprietary. |
| LLM provider agnostic | Anthropic, OpenAI, OpenRouter via env var. No vendor lock-in. |
| Anthropic Console API key required | CLI OAuth tokens don't work with direct API. Documented in README. |
