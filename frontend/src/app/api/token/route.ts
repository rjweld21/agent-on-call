import {
  AccessToken,
  RoomAgentDispatch,
  RoomConfiguration,
} from "livekit-server-sdk";
import { NextRequest, NextResponse } from "next/server";

const VALID_MODELS = [
  "claude-haiku-4-5-20250514",
  "claude-sonnet-4-5-20250514",
  "claude-opus-4-20250514",
];

const DEFAULT_MODEL = "claude-sonnet-4-5-20250514";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const modelParam = searchParams.get("model");
  const verbosityParam = searchParams.get("verbosity");

  // Validate model parameter
  let model = DEFAULT_MODEL;
  if (modelParam) {
    if (!VALID_MODELS.includes(modelParam)) {
      return NextResponse.json(
        { error: `Invalid model: ${modelParam}. Valid models: ${VALID_MODELS.join(", ")}` },
        { status: 400 }
      );
    }
    model = modelParam;
  }

  // Validate verbosity parameter (1-5, default 3)
  let verbosity = 3;
  if (verbosityParam) {
    const parsed = parseInt(verbosityParam, 10);
    if (isNaN(parsed) || parsed < 1 || parsed > 5) {
      return NextResponse.json(
        { error: `Invalid verbosity: ${verbosityParam}. Must be 1-5.` },
        { status: 400 }
      );
    }
    verbosity = parsed;
  }

  const roomName = `room-${Date.now()}`;
  const participantName = `user-${Math.random().toString(36).slice(2, 8)}`;

  const at = new AccessToken(
    process.env.LIVEKIT_API_KEY,
    process.env.LIVEKIT_API_SECRET,
    {
      identity: participantName,
      metadata: JSON.stringify({ model, verbosity }),
    }
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
