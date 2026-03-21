# Agent On Call MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a voice-first AI agent platform where a user joins a LiveKit room in a browser, speaks naturally with an orchestrator agent that can dispatch named sub-agents for concurrent tasks, with a guidance queue for sub-agents needing user input.

**Architecture:** LiveKit Agents Framework (Python) orchestrates a modular voice pipeline: Deepgram Flux for STT, Claude/GPT for LLM reasoning, Cartesia Sonic Turbo for TTS. The orchestrator is a LiveKit Agent that spawns additional agents via the LiveKit Agent Dispatch API. Sub-agents communicate with the orchestrator via LiveKit RPCs. A React-based frontend (using LiveKit's pre-built agent UI components) provides the browser interface.

**Tech Stack:** Python 3.11+, livekit-agents ~1.4, livekit-plugins-deepgram, livekit-plugins-cartesia, livekit-plugins-anthropic, livekit-plugins-openai, livekit-plugins-silero, livekit-plugins-turn-detector, React/Next.js with @livekit/components-react and @agents-ui, Docker, GitHub Actions

**Spec:** `docs/superpowers/specs/2026-03-21-agent-on-call-design.md`

---

## File Structure

```
agent-on-call/
├── LICENSE                          # AGPL v3
├── README.md                        # Project overview, quickstart
├── CLAUDE.md                        # Development standards
├── .env.example                     # Template for API keys
├── .gitignore                       # Python, Node, Docker ignores
├── docker-compose.yml               # LiveKit server + agent worker
├── Dockerfile                       # Agent worker container
├── pyproject.toml                   # Python project config (deps, linting, testing)
├── .github/
│   └── workflows/
│       └── ci.yml                   # Lint, type-check, test, coverage, Docker build
├── src/
│   └── agent_on_call/
│       ├── __init__.py
│       ├── main.py                  # AgentServer entrypoint, session handlers
│       ├── config.py                # Environment variable loading and validation
│       ├── orchestrator.py          # Orchestrator Agent class (voice + coordination)
│       ├── subagent.py              # SubAgent base class and lifecycle
│       ├── guidance_queue.py        # In-memory guidance queue
│       └── messages.py              # RPC message schemas (requests/responses)
├── tests/
│   ├── conftest.py                  # Shared fixtures
│   ├── test_config.py              # Config loading tests
│   ├── test_orchestrator.py        # Orchestrator logic tests
│   ├── test_subagent.py            # Sub-agent lifecycle tests
│   ├── test_guidance_queue.py      # Guidance queue tests
│   └── test_messages.py            # Message schema tests
└── frontend/
    ├── package.json
    ├── tsconfig.json
    ├── next.config.js
    ├── .env.local.example
    └── src/
        └── app/
            ├── layout.tsx
            ├── page.tsx             # Landing page with room join
            └── room/
                └── page.tsx         # LiveKit room with agent UI
```

---

## Milestone 1: Project Scaffolding & CI/CD

### Task 1: Initialize Python project with pyproject.toml

**Files:**
- Create: `pyproject.toml`
- Create: `src/agent_on_call/__init__.py`
- Create: `.gitignore`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "agent-on-call"
version = "0.1.0"
description = "Voice-first AI agent platform with orchestrator and sub-agents"
license = "AGPL-3.0-or-later"
requires-python = ">=3.11"
dependencies = [
    "livekit-agents[deepgram,cartesia,openai,silero,turn-detector,anthropic]~=1.4",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=4.0",
    "pytest-mock>=3.0",
    "black>=24.0",
    "flake8>=7.0",
    "mypy>=1.8",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.black]
line-length = 127

[tool.mypy]
ignore_missing_imports = true
strict = false

[tool.flake8]
max-line-length = 127
max-complexity = 10
```

- [ ] **Step 2: Create package init**

```python
# src/agent_on_call/__init__.py
"""Agent On Call - Voice-first AI agent platform."""

__version__ = "0.1.0"
```

- [ ] **Step 3: Create .gitignore**

```
# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.eggs/
*.egg
.venv/
venv/
.mypy_cache/
.pytest_cache/
htmlcov/
.coverage

# Environment
.env
.env.local

# Node
node_modules/
.next/
out/

# Docker
.docker/

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Superpowers
.superpowers/
```

- [ ] **Step 4: Install dev dependencies and verify**

Run: `cd C:/Users/rjwel/Documents/Programming/agent-on-call && pip install -e ".[dev]"`
Expected: Installation succeeds, all packages resolved

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/agent_on_call/__init__.py .gitignore
git commit -m "feat: initialize Python project with pyproject.toml"
```

---

### Task 2: Create CI/CD pipeline

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Create GitHub Actions workflow**

```yaml
name: CI

on:
  push:
    branches: [master, main]
  pull_request:
    branches: [master, main]

env:
  PYTHON_VERSION: "3.11"

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: pip install -e ".[dev]"

      - name: Lint with flake8
        run: flake8 src/ tests/ --count --show-source --statistics

      - name: Format check with black
        run: black --check src/ tests/

      - name: Type check with mypy
        run: mypy src/

      - name: Run tests with coverage
        run: pytest --cov=src/agent_on_call --cov-report=xml --cov-report=term -v

      - name: Check coverage threshold
        run: pytest --cov=src/agent_on_call --cov-fail-under=80

  docker-build:
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Build Docker image
        run: docker build -t agent-on-call:test .
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add GitHub Actions pipeline for lint, test, coverage, Docker build"
```

---

### Task 3: Add AGPL license and .env.example

**Files:**
- Create: `LICENSE`
- Create: `.env.example`

- [ ] **Step 1: Create AGPL v3 LICENSE file**

Download the standard AGPL v3 text and save as `LICENSE`. Set copyright to `2026 Agent On Call Contributors`.

- [ ] **Step 2: Create .env.example**

```bash
# LiveKit Server
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret

# Speech-to-Text (Deepgram)
DEEPGRAM_API_KEY=your_deepgram_api_key_here

# Text-to-Speech (Cartesia)
CARTESIA_API_KEY=your_cartesia_api_key_here

# LLM Provider: "anthropic" or "openai"
LLM_PROVIDER=anthropic

# Anthropic (if LLM_PROVIDER=anthropic)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# OpenAI (if LLM_PROVIDER=openai)
OPENAI_API_KEY=your_openai_api_key_here
```

- [ ] **Step 3: Commit**

```bash
git add LICENSE .env.example
git commit -m "feat: add AGPL v3 license and .env.example"
```

---

## Milestone 2: Configuration & Basic Agent Connection

### Task 4: Configuration module

**Files:**
- Create: `src/agent_on_call/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_config.py
import os
import pytest
from unittest.mock import patch


class TestConfig:
    def test_load_config_with_all_vars(self):
        from agent_on_call.config import load_config

        env = {
            "LIVEKIT_URL": "ws://localhost:7880",
            "LIVEKIT_API_KEY": "devkey",
            "LIVEKIT_API_SECRET": "secret",
            "DEEPGRAM_API_KEY": "dg_key",
            "CARTESIA_API_KEY": "cart_key",
            "LLM_PROVIDER": "anthropic",
            "ANTHROPIC_API_KEY": "ant_key",
        }
        with patch.dict(os.environ, env, clear=False):
            config = load_config()
            assert config.livekit_url == "ws://localhost:7880"
            assert config.llm_provider == "anthropic"
            assert config.anthropic_api_key == "ant_key"

    def test_load_config_missing_required_var(self):
        from agent_on_call.config import load_config, ConfigError

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ConfigError):
                load_config()

    def test_load_config_openai_provider(self):
        from agent_on_call.config import load_config

        env = {
            "LIVEKIT_URL": "ws://localhost:7880",
            "LIVEKIT_API_KEY": "devkey",
            "LIVEKIT_API_SECRET": "secret",
            "DEEPGRAM_API_KEY": "dg_key",
            "CARTESIA_API_KEY": "cart_key",
            "LLM_PROVIDER": "openai",
            "OPENAI_API_KEY": "oai_key",
        }
        with patch.dict(os.environ, env, clear=False):
            config = load_config()
            assert config.llm_provider == "openai"
            assert config.openai_api_key == "oai_key"

    def test_load_config_missing_llm_key_for_provider(self):
        from agent_on_call.config import load_config, ConfigError

        env = {
            "LIVEKIT_URL": "ws://localhost:7880",
            "LIVEKIT_API_KEY": "devkey",
            "LIVEKIT_API_SECRET": "secret",
            "DEEPGRAM_API_KEY": "dg_key",
            "CARTESIA_API_KEY": "cart_key",
            "LLM_PROVIDER": "anthropic",
            # Missing ANTHROPIC_API_KEY
        }
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ConfigError, match="ANTHROPIC_API_KEY"):
                load_config()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:/Users/rjwel/Documents/Programming/agent-on-call && pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'agent_on_call.config'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/agent_on_call/config.py
"""Configuration loading from environment variables."""

import os
from dataclasses import dataclass


class ConfigError(Exception):
    """Raised when required configuration is missing."""
    pass


@dataclass(frozen=True)
class Config:
    livekit_url: str
    livekit_api_key: str
    livekit_api_secret: str
    deepgram_api_key: str
    cartesia_api_key: str
    llm_provider: str  # "anthropic" or "openai"
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ConfigError(f"Required environment variable {name} is not set")
    return value


def load_config() -> Config:
    livekit_url = _require("LIVEKIT_URL")
    livekit_api_key = _require("LIVEKIT_API_KEY")
    livekit_api_secret = _require("LIVEKIT_API_SECRET")
    deepgram_api_key = _require("DEEPGRAM_API_KEY")
    cartesia_api_key = _require("CARTESIA_API_KEY")

    llm_provider = os.environ.get("LLM_PROVIDER", "anthropic").lower()

    anthropic_api_key = None
    openai_api_key = None

    if llm_provider == "anthropic":
        anthropic_api_key = _require("ANTHROPIC_API_KEY")
    elif llm_provider == "openai":
        openai_api_key = _require("OPENAI_API_KEY")
    else:
        raise ConfigError(f"Unsupported LLM_PROVIDER: {llm_provider}. Use 'anthropic' or 'openai'.")

    return Config(
        livekit_url=livekit_url,
        livekit_api_key=livekit_api_key,
        livekit_api_secret=livekit_api_secret,
        deepgram_api_key=deepgram_api_key,
        cartesia_api_key=cartesia_api_key,
        llm_provider=llm_provider,
        anthropic_api_key=anthropic_api_key,
        openai_api_key=openai_api_key,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py -v`
Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/agent_on_call/config.py tests/test_config.py
git commit -m "feat: add configuration module with env var loading and validation"
```

---

### Task 5: Message schemas for sub-agent communication

**Files:**
- Create: `src/agent_on_call/messages.py`
- Create: `tests/test_messages.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_messages.py
import json


class TestMessages:
    def test_task_request_to_json(self):
        from agent_on_call.messages import TaskRequest

        req = TaskRequest(
            task_id="task-001",
            description="Research the best database for real-time analytics",
            agent_name="Research - DB Selection",
        )
        data = req.to_json()
        parsed = json.loads(data)
        assert parsed["task_id"] == "task-001"
        assert parsed["type"] == "task_request"

    def test_status_update_from_json(self):
        from agent_on_call.messages import StatusUpdate

        data = json.dumps({
            "type": "status_update",
            "task_id": "task-001",
            "status": "working",
            "detail": "Evaluating PostgreSQL vs ClickHouse",
        })
        update = StatusUpdate.from_json(data)
        assert update.task_id == "task-001"
        assert update.status == "working"

    def test_guidance_request_from_json(self):
        from agent_on_call.messages import GuidanceRequest

        data = json.dumps({
            "type": "guidance_request",
            "task_id": "task-001",
            "question": "Should I prioritize read performance or write throughput?",
            "context": "Both PostgreSQL and ClickHouse are viable options.",
        })
        req = GuidanceRequest.from_json(data)
        assert req.question == "Should I prioritize read performance or write throughput?"

    def test_guidance_response_to_json(self):
        from agent_on_call.messages import GuidanceResponse

        resp = GuidanceResponse(
            task_id="task-001",
            answer="Prioritize read performance for our analytics dashboard use case.",
        )
        data = resp.to_json()
        parsed = json.loads(data)
        assert parsed["type"] == "guidance_response"
        assert "read performance" in parsed["answer"]

    def test_task_result_from_json(self):
        from agent_on_call.messages import TaskResult

        data = json.dumps({
            "type": "task_result",
            "task_id": "task-001",
            "result": "Recommend ClickHouse for read-heavy analytics workloads.",
            "status": "done",
        })
        result = TaskResult.from_json(data)
        assert result.status == "done"
        assert "ClickHouse" in result.result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_messages.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
# src/agent_on_call/messages.py
"""RPC message schemas for orchestrator <-> sub-agent communication."""

import json
from dataclasses import dataclass, asdict


@dataclass
class TaskRequest:
    task_id: str
    description: str
    agent_name: str
    type: str = "task_request"

    def to_json(self) -> str:
        return json.dumps(asdict(self))


@dataclass
class StatusUpdate:
    task_id: str
    status: str  # "working", "waiting_for_input", "done"
    detail: str = ""
    type: str = "status_update"

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> "StatusUpdate":
        d = json.loads(data)
        return cls(task_id=d["task_id"], status=d["status"], detail=d.get("detail", ""))


@dataclass
class GuidanceRequest:
    task_id: str
    question: str
    context: str = ""
    type: str = "guidance_request"

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> "GuidanceRequest":
        d = json.loads(data)
        return cls(task_id=d["task_id"], question=d["question"], context=d.get("context", ""))


@dataclass
class GuidanceResponse:
    task_id: str
    answer: str
    type: str = "guidance_response"

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> "GuidanceResponse":
        d = json.loads(data)
        return cls(task_id=d["task_id"], answer=d["answer"])


@dataclass
class TaskResult:
    task_id: str
    result: str
    status: str  # "done"
    type: str = "task_result"

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> "TaskResult":
        d = json.loads(data)
        return cls(task_id=d["task_id"], result=d["result"], status=d["status"])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_messages.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/agent_on_call/messages.py tests/test_messages.py
git commit -m "feat: add RPC message schemas for sub-agent communication"
```

---

### Task 6: Basic agent entrypoint that connects to LiveKit

**Files:**
- Create: `src/agent_on_call/main.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Create test fixtures**

```python
# tests/conftest.py
"""Shared test fixtures."""

import os
import pytest
from unittest.mock import patch


@pytest.fixture
def mock_env():
    """Provide a complete set of environment variables for testing."""
    env = {
        "LIVEKIT_URL": "ws://localhost:7880",
        "LIVEKIT_API_KEY": "devkey",
        "LIVEKIT_API_SECRET": "secret",
        "DEEPGRAM_API_KEY": "test_dg_key",
        "CARTESIA_API_KEY": "test_cart_key",
        "LLM_PROVIDER": "anthropic",
        "ANTHROPIC_API_KEY": "test_ant_key",
    }
    with patch.dict(os.environ, env, clear=False):
        yield env
```

- [ ] **Step 2: Create main.py entrypoint**

```python
# src/agent_on_call/main.py
"""Agent On Call entrypoint — registers agent sessions with LiveKit."""

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentServer, AgentSession
from livekit.plugins import silero

from agent_on_call.orchestrator import OrchestratorAgent

load_dotenv(".env.local")
load_dotenv(".env")

server = AgentServer()


@server.rtc_session(agent_name="orchestrator")
async def orchestrator_session(ctx: agents.JobContext):
    session = AgentSession(
        stt="deepgram/nova-3",
        llm="anthropic/claude-sonnet-4-5-20250514",
        tts="cartesia/sonic-turbo",
        vad=silero.VAD.load(),
    )

    await session.start(
        room=ctx.room,
        agent=OrchestratorAgent(),
    )

    await session.generate_reply(
        instructions="Greet the user. Introduce yourself as the Agent On Call orchestrator. Ask how you can help today."
    )


if __name__ == "__main__":
    agents.cli.run_app(server)
```

- [ ] **Step 3: Commit**

```bash
git add src/agent_on_call/main.py tests/conftest.py
git commit -m "feat: add agent server entrypoint with orchestrator session"
```

---

## Milestone 3: Orchestrator Agent with Voice Pipeline

### Task 7: Orchestrator Agent class

**Files:**
- Create: `src/agent_on_call/orchestrator.py`
- Create: `tests/test_orchestrator.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_orchestrator.py
import pytest


class TestOrchestratorAgent:
    def test_orchestrator_has_instructions(self):
        from agent_on_call.orchestrator import OrchestratorAgent

        agent = OrchestratorAgent()
        assert "orchestrator" in agent.instructions.lower()

    def test_orchestrator_tracks_subagents(self):
        from agent_on_call.orchestrator import OrchestratorAgent

        agent = OrchestratorAgent()
        assert hasattr(agent, "active_subagents")
        assert isinstance(agent.active_subagents, dict)

    def test_orchestrator_has_guidance_queue(self):
        from agent_on_call.orchestrator import OrchestratorAgent

        agent = OrchestratorAgent()
        assert hasattr(agent, "guidance_queue")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_orchestrator.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
# src/agent_on_call/orchestrator.py
"""Orchestrator Agent — voice interface and sub-agent coordination."""

from livekit.agents import Agent

from agent_on_call.guidance_queue import GuidanceQueue

ORCHESTRATOR_INSTRUCTIONS = """You are the Agent On Call orchestrator. You are a helpful AI assistant \
on a voice call with the user.

You can dispatch sub-agents to work on tasks concurrently. When the user asks you to do something \
that would benefit from a dedicated agent (research, code review, writing, analysis), offer to \
spin up a sub-agent for it.

When a sub-agent is waiting for guidance, mention it at a natural break in conversation. \
Do not interrupt the user mid-thought. Wait for a pause or topic transition, then say something like: \
"By the way, [agent name] has a question about [topic] — want to address that now or later?"

Always announce when a new sub-agent joins or when one finishes its work.

Keep your responses conversational and concise — this is a voice call, not a text chat."""


class OrchestratorAgent(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=ORCHESTRATOR_INSTRUCTIONS)
        self.active_subagents: dict[str, dict] = {}
        self.guidance_queue = GuidanceQueue()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_orchestrator.py -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/agent_on_call/orchestrator.py tests/test_orchestrator.py
git commit -m "feat: add OrchestratorAgent with instructions and sub-agent tracking"
```

---

### Task 8: Guidance queue

**Files:**
- Create: `src/agent_on_call/guidance_queue.py`
- Create: `tests/test_guidance_queue.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_guidance_queue.py
import pytest
from agent_on_call.messages import GuidanceRequest


class TestGuidanceQueue:
    def test_enqueue_request(self):
        from agent_on_call.guidance_queue import GuidanceQueue

        queue = GuidanceQueue()
        req = GuidanceRequest(
            task_id="task-001",
            question="Which database?",
            context="Comparing Postgres and ClickHouse",
        )
        queue.enqueue(req)
        assert queue.size() == 1

    def test_dequeue_fifo(self):
        from agent_on_call.guidance_queue import GuidanceQueue

        queue = GuidanceQueue()
        req1 = GuidanceRequest(task_id="task-001", question="Q1")
        req2 = GuidanceRequest(task_id="task-002", question="Q2")
        queue.enqueue(req1)
        queue.enqueue(req2)

        result = queue.dequeue()
        assert result.task_id == "task-001"
        assert queue.size() == 1

    def test_dequeue_empty_returns_none(self):
        from agent_on_call.guidance_queue import GuidanceQueue

        queue = GuidanceQueue()
        assert queue.dequeue() is None

    def test_peek_does_not_remove(self):
        from agent_on_call.guidance_queue import GuidanceQueue

        queue = GuidanceQueue()
        req = GuidanceRequest(task_id="task-001", question="Q1")
        queue.enqueue(req)

        peeked = queue.peek()
        assert peeked is not None
        assert peeked.task_id == "task-001"
        assert queue.size() == 1

    def test_has_pending(self):
        from agent_on_call.guidance_queue import GuidanceQueue

        queue = GuidanceQueue()
        assert not queue.has_pending()

        queue.enqueue(GuidanceRequest(task_id="task-001", question="Q1"))
        assert queue.has_pending()

    def test_remove_by_task_id(self):
        from agent_on_call.guidance_queue import GuidanceQueue

        queue = GuidanceQueue()
        queue.enqueue(GuidanceRequest(task_id="task-001", question="Q1"))
        queue.enqueue(GuidanceRequest(task_id="task-002", question="Q2"))

        queue.remove_by_task_id("task-001")
        assert queue.size() == 1
        assert queue.peek().task_id == "task-002"

    def test_get_summary(self):
        from agent_on_call.guidance_queue import GuidanceQueue

        queue = GuidanceQueue()
        queue.enqueue(GuidanceRequest(task_id="task-001", question="Which database?"))
        queue.enqueue(GuidanceRequest(task_id="task-002", question="Frontend or backend first?"))

        summary = queue.get_summary()
        assert len(summary) == 2
        assert summary[0]["task_id"] == "task-001"
        assert "database" in summary[0]["question"].lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_guidance_queue.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
# src/agent_on_call/guidance_queue.py
"""In-memory guidance queue for sub-agents waiting on user input."""

from collections import deque
from agent_on_call.messages import GuidanceRequest


class GuidanceQueue:
    def __init__(self) -> None:
        self._queue: deque[GuidanceRequest] = deque()

    def enqueue(self, request: GuidanceRequest) -> None:
        self._queue.append(request)

    def dequeue(self) -> GuidanceRequest | None:
        if not self._queue:
            return None
        return self._queue.popleft()

    def peek(self) -> GuidanceRequest | None:
        if not self._queue:
            return None
        return self._queue[0]

    def has_pending(self) -> bool:
        return len(self._queue) > 0

    def size(self) -> int:
        return len(self._queue)

    def remove_by_task_id(self, task_id: str) -> None:
        self._queue = deque(r for r in self._queue if r.task_id != task_id)

    def get_summary(self) -> list[dict]:
        return [
            {"task_id": r.task_id, "question": r.question, "context": r.context}
            for r in self._queue
        ]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_guidance_queue.py -v`
Expected: All 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/agent_on_call/guidance_queue.py tests/test_guidance_queue.py
git commit -m "feat: add in-memory guidance queue for sub-agent input requests"
```

---

## Milestone 4: Sub-Agent Lifecycle

### Task 9: Sub-agent base class and lifecycle

**Files:**
- Create: `src/agent_on_call/subagent.py`
- Create: `tests/test_subagent.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_subagent.py
import pytest


class TestSubAgent:
    def test_subagent_creation(self):
        from agent_on_call.subagent import SubAgentInfo

        info = SubAgentInfo(
            task_id="task-001",
            agent_name="Research - DB Selection",
            description="Research the best database for real-time analytics",
        )
        assert info.task_id == "task-001"
        assert info.status == "working"

    def test_subagent_status_transitions(self):
        from agent_on_call.subagent import SubAgentInfo

        info = SubAgentInfo(
            task_id="task-001",
            agent_name="Research - DB Selection",
            description="Research task",
        )
        assert info.status == "working"

        info.status = "waiting_for_input"
        assert info.status == "waiting_for_input"

        info.status = "done"
        assert info.status == "done"

    def test_subagent_registry_add_and_get(self):
        from agent_on_call.subagent import SubAgentRegistry, SubAgentInfo

        registry = SubAgentRegistry()
        info = SubAgentInfo(
            task_id="task-001",
            agent_name="Research - DB Selection",
            description="Research task",
        )
        registry.add(info)
        assert registry.get("task-001") is info

    def test_subagent_registry_remove(self):
        from agent_on_call.subagent import SubAgentRegistry, SubAgentInfo

        registry = SubAgentRegistry()
        info = SubAgentInfo(task_id="task-001", agent_name="Agent", description="Task")
        registry.add(info)
        registry.remove("task-001")
        assert registry.get("task-001") is None

    def test_subagent_registry_list_active(self):
        from agent_on_call.subagent import SubAgentRegistry, SubAgentInfo

        registry = SubAgentRegistry()
        registry.add(SubAgentInfo(task_id="t1", agent_name="A1", description="T1"))
        registry.add(SubAgentInfo(task_id="t2", agent_name="A2", description="T2"))

        active = registry.list_active()
        assert len(active) == 2

    def test_subagent_registry_list_waiting(self):
        from agent_on_call.subagent import SubAgentRegistry, SubAgentInfo

        registry = SubAgentRegistry()
        info1 = SubAgentInfo(task_id="t1", agent_name="A1", description="T1")
        info2 = SubAgentInfo(task_id="t2", agent_name="A2", description="T2")
        info2.status = "waiting_for_input"
        registry.add(info1)
        registry.add(info2)

        waiting = registry.list_waiting()
        assert len(waiting) == 1
        assert waiting[0].task_id == "t2"

    def test_generate_task_id(self):
        from agent_on_call.subagent import generate_task_id

        id1 = generate_task_id()
        id2 = generate_task_id()
        assert id1 != id2
        assert id1.startswith("task-")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_subagent.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
# src/agent_on_call/subagent.py
"""Sub-agent data model, registry, and lifecycle management."""

import uuid
from dataclasses import dataclass, field


@dataclass
class SubAgentInfo:
    task_id: str
    agent_name: str
    description: str
    status: str = "working"  # "working", "waiting_for_input", "done"
    result: str | None = None


class SubAgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, SubAgentInfo] = {}

    def add(self, info: SubAgentInfo) -> None:
        self._agents[info.task_id] = info

    def get(self, task_id: str) -> SubAgentInfo | None:
        return self._agents.get(task_id)

    def remove(self, task_id: str) -> None:
        self._agents.pop(task_id, None)

    def list_active(self) -> list[SubAgentInfo]:
        return [a for a in self._agents.values() if a.status != "done"]

    def list_waiting(self) -> list[SubAgentInfo]:
        return [a for a in self._agents.values() if a.status == "waiting_for_input"]


def generate_task_id() -> str:
    return f"task-{uuid.uuid4().hex[:8]}"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_subagent.py -v`
Expected: All 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/agent_on_call/subagent.py tests/test_subagent.py
git commit -m "feat: add sub-agent data model and registry"
```

---

## Milestone 5: Docker & Local Setup

### Task 10: Dockerfile for agent worker

**Files:**
- Create: `Dockerfile`

- [ ] **Step 1: Create Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir .

COPY .env* ./

CMD ["python", "-m", "agent_on_call.main", "start"]
```

- [ ] **Step 2: Commit**

```bash
git add Dockerfile
git commit -m "feat: add Dockerfile for agent worker"
```

---

### Task 11: Docker Compose for local development

**Files:**
- Create: `docker-compose.yml`

- [ ] **Step 1: Create docker-compose.yml**

```yaml
version: "3.8"

services:
  livekit:
    image: livekit/livekit-server:latest
    command: --dev
    ports:
      - "7880:7880"   # WebRTC / HTTP
      - "7881:7881"   # WebSocket
    environment:
      - LIVEKIT_KEYS=devkey:secret

  agent:
    build: .
    depends_on:
      - livekit
    env_file:
      - .env
    environment:
      - LIVEKIT_URL=ws://livekit:7880
      - LIVEKIT_API_KEY=devkey
      - LIVEKIT_API_SECRET=secret
    volumes:
      - ./src:/app/src  # Hot reload during development
```

- [ ] **Step 2: Commit**

```bash
git add docker-compose.yml
git commit -m "feat: add docker-compose for local LiveKit + agent development"
```

---

## Milestone 6: Frontend (Browser UI)

### Task 12: Initialize Next.js frontend with LiveKit agent UI

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/next.config.js`
- Create: `frontend/.env.local.example`
- Create: `frontend/src/app/layout.tsx`
- Create: `frontend/src/app/page.tsx`
- Create: `frontend/src/app/room/page.tsx`

- [ ] **Step 1: Initialize frontend project**

Run:
```bash
cd C:/Users/rjwel/Documents/Programming/agent-on-call
mkdir -p frontend
cd frontend
npx create-next-app@latest . --typescript --tailwind --eslint --app --src-dir --no-import-alias
npm install @livekit/components-react livekit-client
```

- [ ] **Step 2: Create .env.local.example**

```bash
# frontend/.env.local.example
NEXT_PUBLIC_LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
```

- [ ] **Step 3: Create room page with LiveKit agent UI**

```tsx
// frontend/src/app/room/page.tsx
"use client";

import {
  LiveKitRoom,
  RoomAudioRenderer,
  useVoiceAssistant,
  BarVisualizer,
  DisconnectButton,
} from "@livekit/components-react";
import "@livekit/components-styles";
import { useCallback, useState } from "react";

function AgentRoom({ token, url }: { token: string; url: string }) {
  return (
    <LiveKitRoom
      token={token}
      serverUrl={url}
      connect={true}
      audio={true}
      style={{ height: "100vh" }}
    >
      <AgentInterface />
      <RoomAudioRenderer />
    </LiveKitRoom>
  );
}

function AgentInterface() {
  const { state, audioTrack } = useVoiceAssistant();

  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      height: "100%",
      gap: "2rem",
    }}>
      <h1>Agent On Call</h1>
      <p>Status: {state}</p>
      <BarVisualizer
        state={state}
        barCount={5}
        trackRef={audioTrack}
        style={{ width: "300px", height: "100px" }}
      />
      <DisconnectButton>Leave Call</DisconnectButton>
    </div>
  );
}

export default function RoomPage() {
  const [token, setToken] = useState<string | null>(null);
  const [connecting, setConnecting] = useState(false);

  const connect = useCallback(async () => {
    setConnecting(true);
    const resp = await fetch("/api/token");
    const data = await resp.json();
    setToken(data.token);
    setConnecting(false);
  }, []);

  if (token) {
    return (
      <AgentRoom
        token={token}
        url={process.env.NEXT_PUBLIC_LIVEKIT_URL || "ws://localhost:7880"}
      />
    );
  }

  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      height: "100vh",
      gap: "1rem",
    }}>
      <h1>Agent On Call</h1>
      <p>Join a call with your AI orchestrator</p>
      <button onClick={connect} disabled={connecting}>
        {connecting ? "Connecting..." : "Start Call"}
      </button>
    </div>
  );
}
```

- [ ] **Step 4: Create token API route**

```tsx
// frontend/src/app/api/token/route.ts
import { AccessToken, RoomAgentDispatch, RoomConfiguration } from "livekit-server-sdk";
import { NextResponse } from "next/server";

export async function GET() {
  const roomName = `room-${Date.now()}`;
  const participantName = `user-${Math.random().toString(36).slice(2, 8)}`;

  const at = new AccessToken(
    process.env.LIVEKIT_API_KEY,
    process.env.LIVEKIT_API_SECRET,
    { identity: participantName }
  );

  at.addGrant({
    room: roomName,
    roomJoin: true,
    canPublish: true,
    canSubscribe: true,
  });

  at.roomConfig = new RoomConfiguration({
    agents: [new RoomAgentDispatch({ agentName: "orchestrator" })],
  });

  const token = await at.toJwt();
  return NextResponse.json({ token, room: roomName });
}
```

- [ ] **Step 5: Install livekit-server-sdk**

Run: `cd frontend && npm install livekit-server-sdk`

- [ ] **Step 6: Commit**

```bash
git add frontend/
git commit -m "feat: add Next.js frontend with LiveKit room and agent UI"
```

---

## Milestone 7: Update README

### Task 13: Write comprehensive README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Write README**

Update `README.md` with:
- Project description and features
- Architecture diagram (text-based)
- Quickstart guide (prerequisites, API keys, docker-compose up, open browser)
- Development setup (running without Docker)
- Configuration reference (all env vars)
- License (AGPL v3)
- Contributing guidelines

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add comprehensive README with quickstart and architecture"
```

---

## Summary

| Milestone | Tasks | What You Can Test |
|-----------|-------|-------------------|
| 1. Scaffolding & CI/CD | 1-3 | CI pipeline runs, project installs |
| 2. Config & Agent Connection | 4-6 | Config loads, agent server starts |
| 3. Orchestrator & Voice | 7-8 | Voice conversation works (needs API keys) |
| 4. Sub-Agent Lifecycle | 9 | Sub-agents can be tracked and managed |
| 5. Docker Setup | 10-11 | `docker-compose up` runs everything |
| 6. Frontend | 12 | Browser UI connects to LiveKit room |
| 7. README | 13 | Documentation complete |

**API keys needed by milestone:**
- Milestones 1-2: None (unit tests with mocks)
- Milestone 3+: Deepgram, Cartesia, Anthropic/OpenAI API keys
- Milestone 5+: Docker Desktop

**Total tasks:** 13
**Estimated test count:** ~30 unit tests across 5 test files
