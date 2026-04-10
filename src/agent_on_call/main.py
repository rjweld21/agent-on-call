"""Agent On Call entrypoint — registers agent sessions with LiveKit."""

import asyncio
import json
import logging
import os
from typing import Any

import httpx
from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import AgentServer, AgentSession
from livekit.plugins import deepgram, cartesia, silero

from agent_on_call.orchestrator import OrchestratorAgent, ORCHESTRATOR_INSTRUCTIONS
from agent_on_call.prompt_builder import PromptBuilder
from agent_on_call.prompt_builder import TEXT_MODE_INSTRUCTION  # noqa: F401
from agent_on_call.prompt_builder import VERBOSITY_PROMPTS  # noqa: F401
from agent_on_call.session_logger import SessionLogger
from agent_on_call.transcript import SessionTranscript
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
            api_key=os.environ.get("OPENAI_API_KEY"),  # type: ignore[arg-type]
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
                model=effective_model, api_key=effective_key,
                client=client, _strict_tool_schema=False,
            )
        else:
            return anthropic_plugin.LLM(
                model=effective_model, api_key=effective_key,
                _strict_tool_schema=False,
            )


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
    """Build agent instructions with a verbosity directive appended.

    DEPRECATED: Use PromptBuilder instead. Kept for backward compatibility
    with _apply_settings_update and tests.
    """
    builder = PromptBuilder()
    builder.set_base_instructions(base_instructions)
    builder.set_verbosity(verbosity)
    return builder.build()


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


def _get_cartesia_api_key() -> str | None:
    """Return the Cartesia API key if set and not a placeholder."""
    api_key = os.environ.get("CARTESIA_API_KEY")
    if not api_key or not api_key.strip():
        return None
    placeholder_values = {
        "placeholder",
        "your_cartesia_api_key_here",
        "sk_test",
        "",
    }
    if api_key.strip().lower() in placeholder_values:
        return None
    return api_key.strip()


def _check_cartesia_status(
    resp_status: int,
    label: str,
    strict: bool = True,
) -> tuple[bool, str] | None:
    """Map an HTTP status code to a TTS failure reason.

    Returns (False, reason) if the status indicates failure, or None
    if the status is OK and checking should continue.

    When strict=True, any 4xx status (besides 401/402/403) is treated
    as a network error. When strict=False, only auth/credit errors
    are flagged (used for the TTS probe where 400 means "auth OK").
    """
    if resp_status in (401, 403):
        logger.warning("Cartesia %s auth failed (HTTP %d)", label, resp_status)
        return (False, "auth_failed")
    if resp_status == 402:
        logger.warning("Cartesia %s has no credits (HTTP 402)", label)
        return (False, "no_credits")
    if strict and resp_status >= 400:
        logger.warning(
            "Cartesia %s returned HTTP %d during health check",
            label,
            resp_status,
        )
        return (False, "network_error")
    return None


def _check_tts_available() -> tuple[bool, str]:
    """Check if TTS is available by validating the Cartesia API key.

    Makes HTTP requests to Cartesia's voices endpoint AND the TTS
    endpoint to verify the key is valid and the account has credits.

    Returns (available, reason) where reason is one of:
    - "" (empty string) if available
    - "no_key" if CARTESIA_API_KEY is not set
    - "auth_failed" if key is invalid (401/403)
    - "no_credits" if account has no credits (402)
    - "network_error" if the API is unreachable
    """
    api_key = _get_cartesia_api_key()
    if not api_key:
        return (False, "no_key")

    headers = {
        "X-API-Key": api_key,
        "Cartesia-Version": "2024-06-10",
    }

    # First: validate the key with the voices endpoint
    try:
        resp = httpx.get(
            "https://api.cartesia.ai/voices",
            headers=headers,
            timeout=5.0,
        )
        failure = _check_cartesia_status(resp.status_code, "API")
        if failure:
            return failure
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPError) as exc:
        logger.warning("Could not reach Cartesia API: %s", exc)
        return (False, "network_error")

    # Second: probe TTS endpoint to verify synthesis credits.
    try:
        tts_resp = httpx.post(
            "https://api.cartesia.ai/tts/bytes",
            headers={**headers, "Content-Type": "application/json"},
            json={
                "transcript": "test",
                "model_id": "sonic-2",
                "voice": {
                    "mode": "id",
                    "id": "a0e99841-438c-4a64-b679-ae501e7d6091",
                },
                "output_format": {
                    "container": "raw",
                    "encoding": "pcm_s16le",
                    "sample_rate": 8000,
                },
            },
            timeout=5.0,
        )
        failure = _check_cartesia_status(
            tts_resp.status_code,
            "TTS",
            strict=False,
        )
        if failure:
            return failure
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPError) as exc:
        logger.warning("Could not reach Cartesia TTS endpoint: %s", exc)
        return (False, "network_error")

    return (True, "")


TTS_STATUS_MESSAGES = {
    "no_key": ("Voice responses unavailable. " "Add a Cartesia API key in settings for voice responses."),
    "auth_failed": ("Voice responses unavailable. " "Cartesia API key is invalid."),
    "no_credits": ("Voice responses unavailable. " "Cartesia account has no credits remaining."),
    "network_error": ("Voice responses unavailable. " "Could not reach Cartesia API."),
}


def _build_session(model: str | None, tts_enabled: bool = True) -> AgentSession:
    """Build an AgentSession with STT, LLM, TTS, VAD, and turn-taking.

    Args:
        model: Optional model override.
        tts_enabled: If False, TTS is omitted and the session runs in text-only mode.
    """
    vad_cfg = DEFAULT_VAD_CONFIG
    tt_cfg = DEFAULT_TURN_TAKING_CONFIG

    tts = None
    if tts_enabled:
        tts = cartesia.TTS(
            api_key=os.environ.get("CARTESIA_API_KEY"),
        )

    return AgentSession(
        stt=deepgram.STT(
            model="nova-3",
            api_key=os.environ.get("DEEPGRAM_API_KEY"),  # type: ignore[arg-type]
        ),
        llm=_build_llm(model=model),
        tts=tts,  # type: ignore[arg-type]
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
    prompt_builder: PromptBuilder | None = None,
) -> tuple[str | None, int, bool]:
    """Apply a parsed settings update to the agent and session.

    Returns (new_model, new_verbosity, changed).
    """
    changed = False

    # Apply verbosity change
    if update["verbosity"] is not None and update["verbosity"] != current_verbosity:
        current_verbosity = update["verbosity"]
        if prompt_builder:
            prompt_builder.set_verbosity(current_verbosity)
            new_instructions = prompt_builder.build()
        else:
            new_instructions = _build_verbosity_instructions(ORCHESTRATOR_INSTRUCTIONS, current_verbosity)
        await agent.update_instructions(new_instructions)
        logger.info("Mid-session verbosity updated to %d", current_verbosity)
        logger.debug("New instructions (verbosity=%d): %s", current_verbosity, new_instructions[:200])
        changed = True

    # Apply model change
    if update["model"] is not None and update["model"] != current_model:
        current_model = update["model"]
        try:
            new_llm = _build_llm(model=current_model)
            session._llm = new_llm  # No public setter in LiveKit SDK — _llm is read each call
            logger.info("Mid-session model updated to %s", current_model)
            logger.debug("LLM instance replaced on session for model=%s", current_model)
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


def _reason_from_status(status_code: int) -> str:
    """Map an HTTP status code to a TTS failure reason string."""
    if status_code in (401, 403):
        return "auth_failed"
    if status_code == 402:
        return "no_credits"
    return "network_error"


def _detect_tts_error(error) -> tuple[bool, str]:
    """Detect if an error is TTS-related and determine the reason.

    Returns (is_tts_error, reason).
    """
    # Check if it's a LiveKit TTSError wrapper
    try:
        from livekit.agents import tts as tts_module

        if isinstance(error, tts_module.TTSError):
            err = error.error
            code = getattr(err, "status_code", 0)
            return (True, _reason_from_status(code))
    except (ImportError, AttributeError):
        pass

    # Check if the error string relates to TTS/Cartesia
    error_str = str(error).lower()
    if "cartesia" in error_str or "tts" in error_str:
        return (True, _reason_from_status_str(error_str))

    # Check for WSServerHandshakeError with status codes
    status = getattr(error, "status", None)
    if status in (401, 402, 403):
        return (True, _reason_from_status(status))

    return (False, "network_error")


def _reason_from_status_str(error_str: str) -> str:
    """Determine TTS failure reason from an error string."""
    if "402" in error_str:
        return "no_credits"
    if "401" in error_str or "403" in error_str:
        return "auth_failed"
    return "network_error"


def _is_tts_greeting_error(error_str: str) -> bool:
    """Check if a greeting error is TTS-related."""
    tts_keywords = ("cartesia", "tts", "402", "handshake")
    return any(kw in error_str for kw in tts_keywords)


def _setup_transcript(ctx, session, session_log):
    """Set up transcript tracking for a session.

    Returns (transcript, transcript_dir).
    """
    transcript = SessionTranscript(session_id=ctx.room.name or "unknown")
    transcript.add_participant(
        ctx.room.local_participant.identity,
        ctx.room.local_participant.name or "Orchestrator",
    )
    for p in ctx.room.remote_participants.values():
        transcript.add_participant(p.identity, p.name or p.identity)

    transcript_dir = os.path.join(".aoc", "transcripts")

    @session.on("user_input_transcription")
    def _on_user_transcription(event):
        if hasattr(event, "text") and event.text:
            transcript.add_entry(
                speaker="user",
                content=event.text,
                entry_type="speech",
            )
            session_log.debug("transcript", f"User: {event.text[:200]}")

    @session.on("agent_speech_committed")
    def _on_agent_speech(event):
        if hasattr(event, "text") and event.text:
            transcript.add_entry(
                speaker="agent",
                content=event.text,
                entry_type="speech",
            )
            session_log.debug("transcript", f"Agent: {event.text[:200]}")

    async def _save_transcript():
        """Save transcript on session end."""
        transcript.end_session()
        try:
            filepath = transcript.save(transcript_dir)
            logger.info("Session transcript saved to %s", filepath)
        except Exception as e:
            logger.error("Failed to save transcript: %s", e)

    ctx.add_shutdown_callback(_save_transcript)
    return transcript


async def _notify_tts_disabled(room, reason: str):
    """Send a tts_status message to the frontend via data channel."""
    tts_status_msg = json.dumps(
        {
            "type": "tts_status",
            "available": False,
            "reason": reason,
        }
    )
    try:
        await room.local_participant.publish_data(
            tts_status_msg.encode(),
            topic="tts_status",
        )
    except Exception as e:
        logger.warning("Failed to send TTS status: %s", e)


def _make_tts_runtime_disabler(session, agent, prompt_builder, room):
    """Create a closure that disables TTS at runtime.

    Returns (disable_fn, is_disabled_fn) where disable_fn(reason)
    disables TTS and is_disabled_fn() returns whether TTS was disabled.
    """
    state = {"disabled": False}

    def disable(reason: str):
        if state["disabled"]:
            return
        logger.warning(
            "TTS failed at runtime (reason: %s) — disabling TTS",
            reason,
        )
        state["disabled"] = True
        session._tts = None
        try:
            session.output.set_audio_enabled(False)
        except Exception as e:
            logger.warning("Failed to disable audio output: %s", e)

        async def _update_tts_instructions():
            prompt_builder.set_tts_available(False)
            new_instr = prompt_builder.build()
            await agent.update_instructions(new_instr)

        asyncio.create_task(_update_tts_instructions())
        asyncio.create_task(_notify_tts_disabled(room, reason))

    def is_disabled():
        return state["disabled"]

    return disable, is_disabled


@server.rtc_session(agent_name="orchestrator")
async def orchestrator_session(ctx: agents.JobContext):  # noqa: C901
    # Read preferences from participant metadata (set by frontend via token API)
    metadata = _get_participant_metadata(ctx)
    selected_model = metadata.get("model")
    verbosity = metadata.get("verbosity", 3)
    if not isinstance(verbosity, int) or verbosity < 1 or verbosity > 5:
        verbosity = 3

    # Check TTS availability
    tts_available, tts_reason = _check_tts_available()
    if not tts_available:
        logger.warning(
            "TTS unavailable (reason: %s) — text-only mode",
            tts_reason,
        )

    # Build agent with PromptBuilder-composed instructions
    agent = OrchestratorAgent()
    prompt_builder = PromptBuilder(token_budget=1500)
    prompt_builder.set_base_instructions(ORCHESTRATOR_INSTRUCTIONS)
    prompt_builder.set_verbosity(verbosity)
    prompt_builder.set_tts_available(tts_available)
    agent._instructions = prompt_builder.build()

    session = _build_session(selected_model, tts_enabled=tts_available)
    await session.start(room=ctx.room, agent=agent)

    if not tts_available:
        session.output.set_audio_enabled(False)

    agent.set_room(ctx.room)
    await ctx.room.local_participant.set_name("Orchestrator")

    # --- Session debug logger ---
    session_log = SessionLogger()
    session_log.start(ctx.room.name or "unknown")
    session_log.info(
        "session",
        f"Model={selected_model}, verbosity={verbosity}, tts={tts_available}",
    )

    async def _close_session_log():
        session_log.close()
        logger.info("Session log saved to %s", session_log.filepath)

    ctx.add_shutdown_callback(_close_session_log)

    # --- Transcript tracking ---
    _setup_transcript(ctx, session, session_log)

    # Notify frontend of TTS status if unavailable
    if not tts_available:
        await _notify_tts_disabled(ctx.room, tts_reason)

    # --- Runtime TTS error handling ---
    disable_tts, is_tts_disabled = _make_tts_runtime_disabler(
        session,
        agent,
        prompt_builder,
        ctx.room,
    )

    @session.on("error")
    def _on_session_error(error):
        session_log.error("session", f"Session error: {error}")
        if is_tts_disabled():
            return
        is_tts_err, reason = _detect_tts_error(error)
        if is_tts_err:
            session_log.warn(
                "tts",
                f"TTS error detected, disabling — reason={reason}",
            )
            disable_tts(reason)

    # --- Mid-session settings via data channel ---
    async def _handle_data_received(data_packet: rtc.DataPacket):
        nonlocal selected_model, verbosity
        update = _parse_settings_update(data_packet.data)
        if update is None:
            try:
                msg = json.loads(data_packet.data)
                session_log.debug(
                    "data_channel",
                    f"Received: type={msg.get('type', 'unknown')}",
                )
            except (json.JSONDecodeError, UnicodeDecodeError):
                session_log.debug("data_channel", "Received non-JSON data")
            return

        session_log.info("data_channel", f"Settings update: {update}")
        selected_model, verbosity, _ = await _apply_settings_update(
            update,
            agent,
            session,
            ctx.room,
            selected_model,
            verbosity,
            prompt_builder=prompt_builder,
        )

    def _on_data_received(data_packet: rtc.DataPacket):
        asyncio.create_task(_handle_data_received(data_packet))

    ctx.room.on("data_received", _on_data_received)

    greeting = "Greet the user. Introduce yourself as the Agent On Call " "orchestrator. Ask how you can help today."
    try:
        await session.generate_reply(instructions=greeting)
    except Exception as e:
        logger.error("generate_reply failed: %s", e)
        if _is_tts_greeting_error(str(e).lower()):
            logger.warning("TTS failure during greeting — disabling TTS")
            disable_tts("no_credits")
            try:
                await session.generate_reply(instructions=greeting)
            except Exception as retry_err:
                logger.error("generate_reply retry failed: %s", retry_err)
        else:
            logger.error("Non-TTS error in generate_reply — not retrying")


if __name__ == "__main__":
    agents.cli.run_app(server)
