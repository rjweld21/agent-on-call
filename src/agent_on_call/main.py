"""Agent On Call entrypoint — registers agent sessions with LiveKit."""

import json
import os

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentServer, AgentSession
from livekit.plugins import deepgram, cartesia, silero

from agent_on_call.orchestrator import OrchestratorAgent

load_dotenv(".env.local")
load_dotenv(".env")

server = AgentServer()

VALID_ANTHROPIC_MODELS = {
    "claude-haiku-4-5-20250514",
    "claude-sonnet-4-5-20250514",
    "claude-opus-4-20250514",
}


def _build_llm(model: str | None = None):
    """Build the LLM plugin based on LLM_PROVIDER env var.

    Args:
        model: Optional model name from participant metadata. If provided and
               valid, overrides the ANTHROPIC_MODEL env var.
    """
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

        PLACEHOLDER_VALUES = {"placeholder", "your_anthropic_api_key_here", ""}
        raw_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        api_key = raw_api_key if raw_api_key not in PLACEHOLDER_VALUES else None
        auth_token = os.environ.get("ANTHROPIC_AUTH_TOKEN")

        # Use provided model if valid, otherwise fall back to env var
        default_model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250514")
        if model and model in VALID_ANTHROPIC_MODELS:
            effective_model = model
        else:
            effective_model = default_model

        # Determine the effective key
        effective_key = api_key or auth_token
        if not effective_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN must be set. "
                "Get an API key at https://console.anthropic.com/settings/keys"
            )

        # If using an OAuth token (starts with sk-ant-oat), create a client
        # that sends it as Bearer auth instead of x-api-key
        if effective_key.startswith("sk-ant-oat"):
            client = anthropic_sdk.AsyncAnthropic(auth_token=effective_key)
            return anthropic_plugin.LLM(
                model=effective_model, api_key=effective_key, client=client
            )
        else:
            return anthropic_plugin.LLM(model=effective_model, api_key=effective_key)


VERBOSITY_PROMPTS = {
    1: "Be extremely concise. Give bare minimum answers. Short, declarative sentences. Skip pleasantries, context, and elaboration.",
    2: "Be brief but complete. Answer with just enough context. No filler or examples unless asked. One or two sentences when possible.",
    3: "Use a natural conversational tone. Provide context when helpful. Explain reasoning briefly.",
    4: "Give thorough explanations. Walk through reasoning step by step. Offer examples and alternatives.",
    5: "Explain everything in full detail. Cover background, context, trade-offs, edge cases, and implications.",
}


def _get_participant_metadata(ctx: agents.JobContext) -> dict:
    """Extract metadata from the first non-agent participant."""
    try:
        for participant in ctx.room.remote_participants.values():
            if participant.metadata:
                meta = json.loads(participant.metadata)
                if isinstance(meta, dict):
                    return meta
    except (json.JSONDecodeError, AttributeError):
        pass
    return {}


@server.rtc_session(agent_name="orchestrator")
async def orchestrator_session(ctx: agents.JobContext):
    # Read preferences from participant metadata (set by frontend via token API)
    metadata = _get_participant_metadata(ctx)
    selected_model = metadata.get("model")
    verbosity = metadata.get("verbosity", 3)
    if not isinstance(verbosity, int) or verbosity < 1 or verbosity > 5:
        verbosity = 3

    # Build agent with verbosity-adjusted instructions
    agent = OrchestratorAgent()
    verbosity_directive = VERBOSITY_PROMPTS.get(verbosity, VERBOSITY_PROMPTS[3])
    agent._raw_instructions = (
        agent.instructions + f"\n\nVerbosity directive: {verbosity_directive}"
    )

    session = AgentSession(
        stt=deepgram.STT(
            model="nova-3",
            api_key=os.environ.get("DEEPGRAM_API_KEY"),
        ),
        llm=_build_llm(model=selected_model),
        tts=cartesia.TTS(
            api_key=os.environ.get("CARTESIA_API_KEY"),
        ),
        vad=silero.VAD.load(),
    )

    await session.start(
        room=ctx.room,
        agent=agent,
    )

    # Set orchestrator display name (must be after session.start connects to room)
    await ctx.room.local_participant.set_name("Orchestrator")

    await session.generate_reply(
        instructions="Greet the user. Introduce yourself as the Agent On Call orchestrator. Ask how you can help today."
    )


if __name__ == "__main__":
    agents.cli.run_app(server)
