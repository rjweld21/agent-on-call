"""Agent On Call entrypoint — registers agent sessions with LiveKit."""

import json
import logging
import os
from typing import Any

from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import AgentServer, AgentSession
from livekit.plugins import deepgram, cartesia, silero

from agent_on_call.orchestrator import OrchestratorAgent, ORCHESTRATOR_INSTRUCTIONS
from agent_on_call.turn_taking import DEFAULT_VAD_CONFIG, DEFAULT_TURN_TAKING_CONFIG

logger = logging.getLogger(__name__)

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
            return anthropic_plugin.LLM(model=effective_model, api_key=effective_key, client=client)
        else:
            return anthropic_plugin.LLM(model=effective_model, api_key=effective_key)


VERBOSITY_PROMPTS = {
    1: (
        "Be extremely concise. Give bare minimum answers. Short, declarative sentences. "
        "Skip pleasantries, context, and elaboration."
    ),
    2: (
        "Be brief but complete. Answer with just enough context. No filler or examples "
        "unless asked. One or two sentences when possible."
    ),
    3: "Use a natural conversational tone. Provide context when helpful. Explain reasoning briefly.",
    4: "Give thorough explanations. Walk through reasoning step by step. Offer examples and alternatives.",
    5: "Explain everything in full detail. Cover background, context, trade-offs, edge cases, and implications.",
}


def _parse_settings_update(data: bytes) -> dict[str, Any] | None:
    """Parse a settings_update data channel message.

    Returns a dict with 'model' and 'verbosity' keys (either may be None if
    not provided or invalid), or None if the message is not a settings_update.
    """
    if not data:
        return None
    try:
        msg = json.loads(data)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None

    if not isinstance(msg, dict) or msg.get("type") != "settings_update":
        return None

    # Validate model
    raw_model = msg.get("model")
    model = raw_model if raw_model in VALID_ANTHROPIC_MODELS else None

    # Validate verbosity
    raw_verbosity = msg.get("verbosity")
    verbosity = None
    if isinstance(raw_verbosity, int) and 1 <= raw_verbosity <= 5:
        verbosity = raw_verbosity

    return {"model": model, "verbosity": verbosity}


def _build_verbosity_instructions(base_instructions: str, verbosity: int) -> str:
    """Build agent instructions with a verbosity directive appended."""
    directive = VERBOSITY_PROMPTS.get(verbosity, VERBOSITY_PROMPTS[3])
    return f"{base_instructions}\n\nVerbosity directive: {directive}"


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


def _build_session(model: str | None) -> AgentSession:
    """Build an AgentSession with STT, LLM, TTS, VAD, and turn-taking."""
    vad_cfg = DEFAULT_VAD_CONFIG
    tt_cfg = DEFAULT_TURN_TAKING_CONFIG
    return AgentSession(
        stt=deepgram.STT(
            model="nova-3",
            api_key=os.environ.get("DEEPGRAM_API_KEY"),
        ),
        llm=_build_llm(model=model),
        tts=cartesia.TTS(
            api_key=os.environ.get("CARTESIA_API_KEY"),
        ),
        vad=silero.VAD.load(
            min_speech_duration=vad_cfg.min_speech_duration,
            min_silence_duration=vad_cfg.min_silence_duration,
            prefix_padding_duration=vad_cfg.prefix_padding_duration,
            activation_threshold=vad_cfg.activation_threshold,
            max_buffered_speech=vad_cfg.max_buffered_speech,
        ),
        min_endpointing_delay=tt_cfg.min_endpointing_delay,
        max_endpointing_delay=tt_cfg.max_endpointing_delay,
        min_interruption_duration=tt_cfg.min_interruption_duration,
        min_interruption_words=tt_cfg.min_interruption_words,
    )


async def _apply_settings_update(
    update: dict[str, Any],
    agent: OrchestratorAgent,
    session: AgentSession,
    room: Any,
    current_model: str | None,
    current_verbosity: int,
) -> tuple[str | None, int, bool]:
    """Apply a parsed settings update to the agent and session.

    Returns (new_model, new_verbosity, changed).
    """
    changed = False

    # Apply verbosity change
    if update["verbosity"] is not None and update["verbosity"] != current_verbosity:
        current_verbosity = update["verbosity"]
        agent._raw_instructions = _build_verbosity_instructions(ORCHESTRATOR_INSTRUCTIONS, current_verbosity)
        logger.info("Mid-session verbosity updated to %d", current_verbosity)
        changed = True

    # Apply model change
    if update["model"] is not None and update["model"] != current_model:
        current_model = update["model"]
        try:
            new_llm = _build_llm(model=current_model)
            session._llm = new_llm
            logger.info("Mid-session model updated to %s", current_model)
            changed = True
        except Exception as e:
            logger.error("Failed to switch model to %s: %s", current_model, e)

    # Send acknowledgment back to frontend
    if changed:
        ack = json.dumps(
            {
                "type": "settings_ack",
                "model": current_model,
                "verbosity": current_verbosity,
            }
        )
        try:
            await room.local_participant.publish_data(
                ack.encode(),
                topic="settings",
            )
        except Exception as e:
            logger.warning("Failed to send settings ack: %s", e)

    return current_model, current_verbosity, changed


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
    agent._raw_instructions = _build_verbosity_instructions(ORCHESTRATOR_INSTRUCTIONS, verbosity)

    session = _build_session(selected_model)

    await session.start(room=ctx.room, agent=agent)

    # Set orchestrator display name (must be after session.start connects to room)
    await ctx.room.local_participant.set_name("Orchestrator")

    # --- Mid-session settings via data channel ---
    async def _on_data_received(data_packet: rtc.DataPacket):
        """Handle settings updates sent by the frontend via data channel."""
        nonlocal selected_model, verbosity

        update = _parse_settings_update(data_packet.data)
        if update is None:
            return

        selected_model, verbosity, _ = await _apply_settings_update(
            update, agent, session, ctx.room, selected_model, verbosity
        )

    ctx.room.on("data_received", _on_data_received)

    await session.generate_reply(
        instructions=("Greet the user. Introduce yourself as the Agent On Call " "orchestrator. Ask how you can help today.")
    )


if __name__ == "__main__":
    agents.cli.run_app(server)
