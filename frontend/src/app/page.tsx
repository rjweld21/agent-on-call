"use client";

import {
  LiveKitRoom,
  RoomAudioRenderer,
  useVoiceAssistant,
  BarVisualizer,
  DisconnectButton,
  useParticipants,
  useLocalParticipant,
} from "@livekit/components-react";
import "@livekit/components-styles";
import { useCallback, useState, useEffect, useRef } from "react";

interface TranscriptEntry {
  speaker: "user" | "agent";
  text: string;
  timestamp: Date;
}

function MicMonitor() {
  const { microphoneTrack } = useLocalParticipant();
  const [audioLevel, setAudioLevel] = useState(0);
  const [micActive, setMicActive] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animFrameRef = useRef<number>(0);

  useEffect(() => {
    if (!microphoneTrack?.track?.mediaStream) {
      setMicActive(false);
      return;
    }

    setMicActive(true);
    const audioCtx = new AudioContext();
    const source = audioCtx.createMediaStreamSource(microphoneTrack.track.mediaStream);
    const analyser = audioCtx.createAnalyser();
    analyser.fftSize = 256;
    source.connect(analyser);

    const dataArray = new Uint8Array(analyser.frequencyBinCount);

    const draw = () => {
      analyser.getByteFrequencyData(dataArray);
      const avg = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;
      setAudioLevel(avg);

      const canvas = canvasRef.current;
      if (canvas) {
        const ctx = canvas.getContext("2d");
        if (ctx) {
          ctx.fillStyle = "#1e293b";
          ctx.fillRect(0, 0, canvas.width, canvas.height);
          const barWidth = (canvas.width / dataArray.length) * 2.5;
          let x = 0;
          for (let i = 0; i < dataArray.length; i++) {
            const barHeight = (dataArray[i] / 255) * canvas.height;
            const hue = (dataArray[i] / 255) * 120;
            ctx.fillStyle = `hsl(${hue}, 80%, 50%)`;
            ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
            x += barWidth + 1;
          }
        }
      }

      animFrameRef.current = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      cancelAnimationFrame(animFrameRef.current);
      audioCtx.close();
    };
  }, [microphoneTrack?.track?.mediaStream]);

  return (
    <div style={{ width: "100%", maxWidth: "500px" }}>
      <h3 style={{ fontSize: "0.85rem", color: "#94a3b8", marginBottom: "0.4rem" }}>
        Microphone {micActive ? (
          <span style={{ color: "#22c55e" }}>Active</span>
        ) : (
          <span style={{ color: "#ef4444" }}>Not detected</span>
        )}
        {micActive && (
          <span style={{ marginLeft: "1rem", color: audioLevel > 10 ? "#22c55e" : "#ef4444" }}>
            Level: {Math.round(audioLevel)}
          </span>
        )}
      </h3>
      {/* Audio level bar */}
      <div style={{
        width: "100%", height: "20px", background: "#0f172a",
        borderRadius: "6px", overflow: "hidden", border: "1px solid #334155",
        marginBottom: "0.5rem",
      }}>
        <div style={{
          width: `${Math.min((audioLevel / 80) * 100, 100)}%`,
          height: "100%",
          background: audioLevel > 40 ? "#22c55e" : audioLevel > 10 ? "#f59e0b" : "#ef4444",
          transition: "width 0.05s ease-out",
          borderRadius: "6px",
        }} />
      </div>
      {/* Frequency visualizer */}
      <canvas ref={canvasRef} width={500} height={60} style={{
        width: "100%", height: "60px",
        border: "1px solid #334155", borderRadius: "6px",
      }} />
      <p style={{ color: "#64748b", fontSize: "0.7rem", marginTop: "0.3rem" }}>
        {audioLevel > 10 ? "Mic is picking up audio" : "Speak to see audio levels..."}
      </p>
    </div>
  );
}

function AgentInterface() {
  const { state, audioTrack, agent } = useVoiceAssistant();
  const participants = useParticipants();
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([]);
  const transcriptRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!agent?.participant) return;
    return () => {};
  }, [agent]);

  useEffect(() => {
    if (transcriptRef.current) {
      transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
    }
  }, [transcript]);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "flex-start",
        height: "100%",
        gap: "1.2rem",
        fontFamily: "system-ui, sans-serif",
        color: "#e2e8f0",
        padding: "1.5rem",
        overflow: "auto",
      }}
    >
      <h1 style={{ fontSize: "1.8rem", fontWeight: "bold", margin: 0 }}>Agent On Call</h1>
      <p style={{ color: "#94a3b8", margin: 0 }}>
        Agent Status:{" "}
        <span
          style={{
            color:
              state === "speaking" ? "#22c55e"
                : state === "listening" ? "#3b82f6"
                : state === "connecting" ? "#f59e0b"
                : "#94a3b8",
            fontWeight: "bold",
          }}
        >
          {state}
        </span>
      </p>

      <BarVisualizer
        state={state}
        barCount={5}
        trackRef={audioTrack}
        style={{ width: "300px", height: "60px" }}
      />

      {/* Mic Monitor */}
      <MicMonitor />

      {/* Participants */}
      <div style={{ width: "100%", maxWidth: "500px" }}>
        <h3 style={{ fontSize: "0.85rem", color: "#94a3b8", marginBottom: "0.4rem" }}>
          Participants ({participants.length})
        </h3>
        <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
          {participants.map((p) => (
            <li key={p.identity} style={{
              padding: "0.2rem 0.6rem", fontSize: "0.85rem",
              color: p.isAgent ? "#fcd34d" : "#e2e8f0",
            }}>
              {p.isAgent ? "\u{1F916} " : "\u{1F464} "}
              {p.name || p.identity}
            </li>
          ))}
        </ul>
      </div>

      {/* Transcript */}
      <div ref={transcriptRef} style={{
        width: "100%", maxWidth: "500px", maxHeight: "200px", overflowY: "auto",
        border: "1px solid #334155", borderRadius: "8px", padding: "0.8rem",
        background: "#1e293b",
      }}>
        <h3 style={{ fontSize: "0.85rem", color: "#94a3b8", marginBottom: "0.5rem" }}>
          Transcript
        </h3>
        {transcript.length === 0 ? (
          <p style={{ color: "#475569", fontSize: "0.8rem", fontStyle: "italic" }}>
            Speak to start the conversation...
          </p>
        ) : (
          transcript.map((entry, i) => (
            <div key={i} style={{
              padding: "0.3rem 0", fontSize: "0.85rem",
              borderBottom: i < transcript.length - 1 ? "1px solid #1e293b" : "none",
            }}>
              <span style={{
                color: entry.speaker === "agent" ? "#fcd34d" : "#60a5fa",
                fontWeight: "bold", marginRight: "0.5rem",
              }}>
                {entry.speaker === "agent" ? "Agent:" : "You:"}
              </span>
              <span style={{ color: "#cbd5e1" }}>{entry.text}</span>
            </div>
          ))
        )}
      </div>

      <DisconnectButton style={{
        padding: "0.5rem 1.5rem", borderRadius: "8px",
        border: "1px solid #dc2626", background: "#7f1d1d",
        color: "#fca5a5", cursor: "pointer", fontSize: "0.9rem",
      }}>
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
    } finally {
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
    <div style={{
      display: "flex", flexDirection: "column", alignItems: "center",
      justifyContent: "center", height: "100vh", gap: "1.5rem",
      background: "#0f172a", fontFamily: "system-ui, sans-serif", color: "#e2e8f0",
    }}>
      <h1 style={{ fontSize: "2.5rem", fontWeight: "bold" }}>Agent On Call</h1>
      <p style={{ color: "#94a3b8", fontSize: "1.1rem" }}>
        Join a call with your AI orchestrator
      </p>
      <button
        onClick={connect}
        disabled={connecting}
        style={{
          padding: "0.8rem 2rem", borderRadius: "10px", border: "none",
          background: connecting ? "#475569" : "#6366f1", color: "white",
          fontSize: "1rem", cursor: connecting ? "default" : "pointer",
          fontWeight: "bold",
        }}
      >
        {connecting ? "Connecting..." : "Start Call"}
      </button>
    </div>
  );
}
