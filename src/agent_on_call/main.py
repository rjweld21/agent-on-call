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
