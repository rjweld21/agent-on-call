"""Agent On Call entrypoint — registers agent sessions with LiveKit."""

import os

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentServer, AgentSession
from livekit.plugins import deepgram, cartesia, silero

from agent_on_call.orchestrator import OrchestratorAgent

load_dotenv(".env.local")
load_dotenv(".env")

server = AgentServer()


def _build_llm():
    """Build the LLM plugin based on LLM_PROVIDER env var."""
    provider = os.environ.get("LLM_PROVIDER", "anthropic").lower()
    if provider == "openai":
        from livekit.plugins import openai

        return openai.LLM(
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            api_key=os.environ.get("OPENAI_API_KEY"),
        )
    else:
        from livekit.plugins import anthropic as anthropic_plugin
        import anthropic as anthropic_sdk

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        auth_token = os.environ.get("ANTHROPIC_AUTH_TOKEN")
        model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250514")

        if api_key:
            # Standard Console API key — use directly
            return anthropic_plugin.LLM(model=model, api_key=api_key)
        elif auth_token:
            # OAuth token (Claude CLI) — needs Bearer auth, not x-api-key
            client = anthropic_sdk.AsyncAnthropic(
                auth_token=auth_token,
            )
            return anthropic_plugin.LLM(model=model, client=client)
        else:
            raise RuntimeError(
                "ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN must be set. "
                "Get an API key at https://console.anthropic.com/settings/keys"
            )


@server.rtc_session(agent_name="orchestrator")
async def orchestrator_session(ctx: agents.JobContext):
    session = AgentSession(
        stt=deepgram.STT(
            model="nova-3",
            api_key=os.environ.get("DEEPGRAM_API_KEY"),
        ),
        llm=_build_llm(),
        tts=cartesia.TTS(
            api_key=os.environ.get("CARTESIA_API_KEY"),
        ),
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
