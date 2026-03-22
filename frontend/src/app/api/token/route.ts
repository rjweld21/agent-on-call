import {
  AccessToken,
  RoomAgentDispatch,
  RoomConfiguration,
} from "livekit-server-sdk";
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
  return NextResponse.json({
    token,
    room: roomName,
    url: process.env.NEXT_PUBLIC_LIVEKIT_URL,
  });
}
