"use client";

import {
  LiveKitRoom,
  RoomAudioRenderer,
  useVoiceAssistant,
  BarVisualizer,
  DisconnectButton,
  useParticipants,
} from "@livekit/components-react";
import "@livekit/components-styles";
import { useCallback, useState } from "react";

function AgentInterface() {
  const { state, audioTrack } = useVoiceAssistant();
  const participants = useParticipants();

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        height: "100%",
        gap: "2rem",
        fontFamily: "system-ui, sans-serif",
        color: "#e2e8f0",
      }}
    >
      <h1 style={{ fontSize: "2rem", fontWeight: "bold" }}>Agent On Call</h1>
      <p style={{ color: "#94a3b8" }}>
        Status:{" "}
        <span
          style={{
            color:
              state === "speaking"
                ? "#22c55e"
                : state === "listening"
                  ? "#3b82f6"
                  : "#94a3b8",
          }}
        >
          {state}
        </span>
      </p>

      <BarVisualizer
        state={state}
        barCount={5}
        trackRef={audioTrack}
        style={{ width: "300px", height: "100px" }}
      />

      <div style={{ marginTop: "1rem" }}>
        <h3
          style={{
            fontSize: "0.9rem",
            color: "#94a3b8",
            marginBottom: "0.5rem",
          }}
        >
          Participants ({participants.length})
        </h3>
        <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
          {participants.map((p) => (
            <li
              key={p.identity}
              style={{
                padding: "0.3rem 0.8rem",
                fontSize: "0.85rem",
                color: p.isAgent ? "#fcd34d" : "#e2e8f0",
              }}
            >
              {p.isAgent ? "\u{1F916} " : "\u{1F464} "}
              {p.name || p.identity}
            </li>
          ))}
        </ul>
      </div>

      <DisconnectButton
        style={{
          marginTop: "1rem",
          padding: "0.5rem 1.5rem",
          borderRadius: "8px",
          border: "1px solid #dc2626",
          background: "#7f1d1d",
          color: "#fca5a5",
          cursor: "pointer",
          fontSize: "0.9rem",
        }}
      >
        Leave Call
      </DisconnectButton>
    </div>
  );
}

export default function Home() {
  const [connectionDetails, setConnectionDetails] = useState<{
    token: string;
    url: string;
  } | null>(null);
  const [connecting, setConnecting] = useState(false);

  const connect = useCallback(async () => {
    setConnecting(true);
    try {
      const resp = await fetch("/api/token");
      const data = await resp.json();
      setConnectionDetails({ token: data.token, url: data.url });
    } catch (err) {
      console.error("Failed to get token:", err);
      setConnecting(false);
    }
  }, []);

  const disconnect = useCallback(() => {
    setConnectionDetails(null);
  }, []);

  if (connectionDetails) {
    return (
      <div style={{ height: "100vh", background: "#0f172a" }}>
        <LiveKitRoom
          token={connectionDetails.token}
          serverUrl={connectionDetails.url}
          connect={true}
          audio={true}
          onDisconnected={disconnect}
          style={{ height: "100%" }}
        >
          <AgentInterface />
          <RoomAudioRenderer />
        </LiveKitRoom>
      </div>
    );
  }

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        height: "100vh",
        gap: "1.5rem",
        background: "#0f172a",
        fontFamily: "system-ui, sans-serif",
        color: "#e2e8f0",
      }}
    >
      <h1 style={{ fontSize: "2.5rem", fontWeight: "bold" }}>Agent On Call</h1>
      <p style={{ color: "#94a3b8", fontSize: "1.1rem" }}>
        Join a call with your AI orchestrator
      </p>
      <button
        onClick={connect}
        disabled={connecting}
        style={{
          padding: "0.8rem 2rem",
          borderRadius: "10px",
          border: "none",
          background: connecting ? "#475569" : "#6366f1",
          color: "white",
          fontSize: "1rem",
          cursor: connecting ? "default" : "pointer",
          fontWeight: "bold",
        }}
      >
        {connecting ? "Connecting..." : "Start Call"}
      </button>
    </div>
  );
}
