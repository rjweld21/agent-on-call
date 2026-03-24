# Agent On Call

A voice-first AI agent platform where you join a call, talk naturally with an AI orchestrator, and it works on tasks in isolated workspace environments — cloning repos, running commands, reading and writing files.

## How It Works

1. Start the system locally with `docker-compose up`
2. Start the frontend with `cd frontend && npm run dev`
3. Open http://localhost:3000 in your browser
4. Click "Start Call" and grant microphone access
5. Talk to the orchestrator — ask it to create workspaces, clone repos, run tests
6. Type messages or paste URLs in the text input box
7. See the live transcript with timestamps

## Features

- **Voice conversation** — Natural speech-to-text and text-to-speech via Deepgram and Cartesia
- **Text input** — Paste URLs, code snippets, or type messages alongside voice
- **Workspace isolation** — Each project runs in its own Docker container with persistent storage
- **Agent tools** — The orchestrator can run shell commands, read/write files, clone repos
- **Live transcript** — See everything said with timestamps
- **Mic monitor** — Visual audio level indicator for debugging
- **LLM flexibility** — Use Claude (Anthropic) or GPT (OpenAI) via env var config

## Architecture

```
User (Browser)
    |
    | WebRTC Audio + Data Channel (text input)
    |
LiveKit Server (Docker)
    |
    | LiveKit Agents SDK
    |
Orchestrator Agent
    ├── STT (Deepgram Flux) — speech to text
    ├── LLM (Claude / GPT) — reasoning + tool calling
    ├── TTS (Cartesia Sonic Turbo) — text to speech
    └── Workspace Containers (Docker)
        ├── Shell command execution
        ├── File read/write
        ├── Git operations
        └── Persistent volumes per project
```

## Quickstart

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Node.js 18+](https://nodejs.org/) (for frontend)
- API keys (see below)

### 1. Clone and configure

```bash
git clone https://github.com/rjweld21/agent-on-call.git
cd agent-on-call
cp .env.example .env
```

### 2. Get API keys

You need three API keys. All have free tiers:

| Service | What It Does | Sign Up | Free Tier |
|---------|-------------|---------|-----------|
| **Deepgram** | Speech-to-Text | [deepgram.com](https://deepgram.com) | $200 free credits |
| **Cartesia** | Text-to-Speech | [cartesia.ai](https://cartesia.ai) | Free tier available |
| **Anthropic** | LLM (Claude) | [console.anthropic.com](https://console.anthropic.com) | Pay-per-use |

Edit your `.env` file and replace the placeholder values:

```bash
DEEPGRAM_API_KEY=your_key_here
CARTESIA_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here    # From console.anthropic.com (sk-ant-api03-...)
```

**Using OpenAI instead of Anthropic?** Set `LLM_PROVIDER=openai` and provide `OPENAI_API_KEY` instead.

### 3. Build the workspace image

```bash
docker build -t aoc-workspace-dev workspace/
```

### 4. Start the backend

```bash
docker-compose up -d
```

This starts:
- **LiveKit server** on port 7880 (WebRTC audio transport)
- **Agent worker** (orchestrator, connects to LiveKit automatically)

### 5. Start the frontend

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

### 6. Join a call

Open http://localhost:3000, click **Start Call**, and start talking.

**Try saying:**
- "Create a workspace called my-project"
- "Clone the agent-on-call repo from GitHub"
- "List the files in the workspace"
- "Run python --version"

## Configuration Reference

All configuration is via environment variables in `.env`:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LIVEKIT_URL` | Yes | `ws://localhost:7880` | LiveKit server URL |
| `LIVEKIT_API_KEY` | Yes | `devkey` | LiveKit API key |
| `LIVEKIT_API_SECRET` | Yes | `secret` | LiveKit API secret |
| `DEEPGRAM_API_KEY` | Yes | — | Deepgram API key for speech-to-text |
| `CARTESIA_API_KEY` | Yes | — | Cartesia API key for text-to-speech |
| `LLM_PROVIDER` | No | `anthropic` | LLM provider: `anthropic` or `openai` |
| `ANTHROPIC_API_KEY` | If Anthropic | — | Anthropic Console API key |
| `ANTHROPIC_MODEL` | No | `claude-sonnet-4-20250514` | Anthropic model to use |
| `OPENAI_API_KEY` | If OpenAI | — | OpenAI API key |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | OpenAI model to use |

## Development Setup (Without Docker)

```bash
# Install Python dependencies
pip install -e ".[dev]"

# Start LiveKit server locally
livekit-server --dev

# In another terminal, start the agent
python -m agent_on_call.main dev

# In another terminal, start the frontend
cd frontend && npm run dev
```

### Running Tests

```bash
pytest -v --cov=src/agent_on_call
```

### Code Quality

```bash
black src/ tests/          # Format
flake8 src/ tests/         # Lint
mypy src/                  # Type check
```

## Project Structure

```
agent-on-call/
├── src/agent_on_call/
│   ├── main.py            # LiveKit agent server entrypoint
│   ├── config.py          # Environment variable loading
│   ├── orchestrator.py    # Orchestrator agent (voice + tools)
│   ├── workspace.py       # Docker workspace container management
│   ├── subagent.py        # Sub-agent data model and registry
│   ├── guidance_queue.py  # Queue for sub-agents needing user input
│   └── messages.py        # RPC message schemas
├── tests/                 # Unit tests (20 tests)
├── frontend/              # Next.js browser UI
│   └── src/app/
│       ├── page.tsx       # Main call interface
│       ├── test/page.tsx  # Audio test page
│       └── api/token/     # LiveKit token generation
├── workspace/
│   └── Dockerfile         # Workspace container (parameterized base image)
├── Dockerfile             # Agent worker container
├── docker-compose.yml     # Local development stack
├── .env.example           # Configuration template
└── .github/workflows/     # CI/CD pipeline
```

## Estimated Costs

| Service | Cost | Notes |
|---------|------|-------|
| Deepgram STT | ~$0.008/min | $200 free credits on signup |
| Claude Sonnet | ~$0.01-0.03/min | ~500 tokens per turn |
| GPT-4o-mini | ~$0.001-0.003/min | 10x cheaper alternative |
| Cartesia TTS | ~$0.005/min | Free tier available |
| **Total** | **~$0.02-0.04/min** | With Claude Sonnet |

A 10-minute test call costs roughly $0.20-0.40.

## Roadmap

- [ ] Sub-agent dispatch — spawn named agents for concurrent tasks
- [ ] Session persistence — resume where you left off
- [ ] Terminal output panel — see command output in the UI
- [ ] Audio echo cancellation — reduce feedback on speakerphone
- [ ] Discord connector — join Discord voice channels
- [ ] OpenRouter support — 100+ LLM models via single API key
- [ ] Managed cloud product — hosted multi-tenant service

## License

[AGPL-3.0](LICENSE) — You can use, modify, and self-host Agent On Call. If you modify it and run it as a service, you must open-source your modifications.
