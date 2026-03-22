# Agent On Call

A voice-first AI agent platform where you join a call and talk naturally with an AI orchestrator that can dispatch specialized sub-agents to work on tasks concurrently.

## How It Works

1. You start the system locally with `docker-compose up`
2. Open a browser and join a LiveKit room
3. Speak naturally — the orchestrator listens, reasons, and responds
4. Ask it to do things — it spawns named sub-agents visible in the participant list
5. Sub-agents work independently and report back when done

## Architecture

```
User (Browser) ←→ LiveKit Server ←→ Orchestrator Agent
                                         ├── STT (Deepgram Flux)
                                         ├── LLM (Claude / GPT)
                                         ├── TTS (Cartesia Sonic Turbo)
                                         └── Sub-Agents (named participants)
```

## Quickstart

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
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
# Required — get these from the services above
DEEPGRAM_API_KEY=your_key_here
CARTESIA_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here    # From console.anthropic.com (sk-ant-api03-...)
```

**Using OpenAI instead of Anthropic?** Set `LLM_PROVIDER=openai` and provide `OPENAI_API_KEY` instead.

### 3. Start the system

```bash
docker-compose up
```

This starts:
- **LiveKit server** on port 7880 (handles WebRTC audio transport)
- **Agent worker** (your AI orchestrator, connects to LiveKit automatically)

### 4. Join a call

Open your browser to the frontend URL (see M4 — coming soon).

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
| `ANTHROPIC_API_KEY` | If using Anthropic | — | Anthropic Console API key |
| `OPENAI_API_KEY` | If using OpenAI | — | OpenAI API key |

## Development Setup (Without Docker)

If you prefer running without Docker:

```bash
# Install Python dependencies
pip install -e ".[dev]"

# Start LiveKit server locally (requires livekit-server installed)
livekit-server --dev

# In another terminal, start the agent
python -m agent_on_call.main dev
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
│   ├── orchestrator.py    # Orchestrator agent (voice + coordination)
│   ├── subagent.py        # Sub-agent data model and registry
│   ├── guidance_queue.py  # Queue for sub-agents needing user input
│   └── messages.py        # RPC message schemas
├── tests/                 # Unit tests
├── frontend/              # Next.js browser UI (coming soon)
├── Dockerfile             # Agent worker container
├── docker-compose.yml     # Local development stack
└── .env.example           # Configuration template
```

## License

[AGPL-3.0](LICENSE) — You can use, modify, and self-host Agent On Call. If you modify it and run it as a service, you must open-source your modifications.
