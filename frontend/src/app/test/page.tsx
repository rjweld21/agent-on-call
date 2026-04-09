"use client";

import {
  LiveKitRoom,
  useLocalParticipant,
  useParticipants,
} from "@livekit/components-react";
import "@livekit/components-styles";
import { useCallback, useState, useEffect, useRef } from "react";
import Link from "next/link";

function AudioTest() {
  const { localParticipant, microphoneTrack } = useLocalParticipant();
  const participants = useParticipants();
  const [audioLevel, setAudioLevel] = useState(0);
  const [isPublishing, setIsPublishing] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animFrameRef = useRef<number>(0);

  // Monitor audio levels from the microphone track
  useEffect(() => {
    if (!microphoneTrack?.track?.mediaStream) return;

    const audioCtx = new AudioContext();
    const source = audioCtx.createMediaStreamSource(microphoneTrack.track.mediaStream);
    const analyser = audioCtx.createAnalyser();
    analyser.fftSize = 256;
    source.connect(analyser);
    analyserRef.current = analyser;

    const dataArray = new Uint8Array(analyser.frequencyBinCount);

    const draw = () => {
      analyser.getByteFrequencyData(dataArray);
      const avg = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;
      setAudioLevel(avg);

      // Draw waveform on canvas
      const canvas = canvasRef.current;
      if (canvas) {
        const ctx = canvas.getContext("2d");
        if (ctx) {
          ctx.fillStyle = "#0f172a";
          ctx.fillRect(0, 0, canvas.width, canvas.height);

          const barWidth = (canvas.width / dataArray.length) * 2.5;
          let x = 0;
          for (let i = 0; i < dataArray.length; i++) {
            const barHeight = (dataArray[i] / 255) * canvas.height;
            const hue = (dataArray[i] / 255) * 120; // red to green
            ctx.fillStyle = `hsl(${hue}, 80%, 50%)`;
            ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
            x += barWidth + 1;
          }
        }
      }

      animFrameRef.current = requestAnimationFrame(draw);
    };

    draw();
    // Defer state updates to avoid synchronous setState in effect body
    const publishId = requestAnimationFrame(() => setIsPublishing(true));

    return () => {
      cancelAnimationFrame(publishId);
      cancelAnimationFrame(animFrameRef.current);
      audioCtx.close();
      requestAnimationFrame(() => setIsPublishing(false));
    };
  }, [microphoneTrack?.track?.mediaStream]);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "flex-start",
        height: "100%",
        gap: "1.5rem",
        fontFamily: "system-ui, sans-serif",
        color: "#e2e8f0",
        padding: "2rem",
      }}
    >
      <h1 style={{ fontSize: "1.8rem", fontWeight: "bold", margin: 0 }}>
        Audio Test
      </h1>
      <p style={{ color: "#94a3b8", margin: 0, textAlign: "center" }}>
        This page tests your microphone through LiveKit.
        <br />
        No agent connection needed.
      </p>

      {/* Status */}
      <div
        style={{
          display: "flex",
          gap: "2rem",
          flexWrap: "wrap",
          justifyContent: "center",
        }}
      >
        <div style={{ textAlign: "center" }}>
          <div style={{ color: "#94a3b8", fontSize: "0.8rem" }}>Mic Publishing</div>
          <div
            style={{
              color: isPublishing ? "#22c55e" : "#ef4444",
              fontWeight: "bold",
              fontSize: "1.1rem",
            }}
          >
            {isPublishing ? "YES" : "NO"}
          </div>
        </div>
        <div style={{ textAlign: "center" }}>
          <div style={{ color: "#94a3b8", fontSize: "0.8rem" }}>Audio Level</div>
          <div
            style={{
              color: audioLevel > 10 ? "#22c55e" : "#ef4444",
              fontWeight: "bold",
              fontSize: "1.1rem",
            }}
          >
            {Math.round(audioLevel)}
          </div>
        </div>
        <div style={{ textAlign: "center" }}>
          <div style={{ color: "#94a3b8", fontSize: "0.8rem" }}>Participants</div>
          <div style={{ color: "#60a5fa", fontWeight: "bold", fontSize: "1.1rem" }}>
            {participants.length}
          </div>
        </div>
      </div>

      {/* Audio Level Bar */}
      <div
        style={{
          width: "100%",
          maxWidth: "400px",
          height: "30px",
          background: "#1e293b",
          borderRadius: "8px",
          overflow: "hidden",
          border: "1px solid #334155",
        }}
      >
        <div
          style={{
            width: `${Math.min((audioLevel / 80) * 100, 100)}%`,
            height: "100%",
            background:
              audioLevel > 40
                ? "#22c55e"
                : audioLevel > 10
                  ? "#f59e0b"
                  : "#ef4444",
            transition: "width 0.05s ease-out",
            borderRadius: "8px",
          }}
        />
      </div>
      <p style={{ color: "#64748b", fontSize: "0.75rem", margin: 0 }}>
        {audioLevel > 10
          ? "Microphone is picking up audio!"
          : "Speak into your microphone... (bar should move)"}
      </p>

      {/* Frequency Visualizer */}
      <canvas
        ref={canvasRef}
        width={400}
        height={120}
        style={{
          border: "1px solid #334155",
          borderRadius: "8px",
          maxWidth: "100%",
        }}
      />

      {/* Participant List */}
      <div style={{ width: "100%", maxWidth: "400px" }}>
        <h3 style={{ fontSize: "0.85rem", color: "#94a3b8", marginBottom: "0.4rem" }}>
          Participants in room
        </h3>
        <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
          {participants.map((p) => (
            <li
              key={p.identity}
              style={{
                padding: "0.2rem 0.5rem",
                fontSize: "0.85rem",
                color: p.isAgent ? "#fcd34d" : "#e2e8f0",
              }}
            >
              {p.isAgent ? "\u{1F916} " : "\u{1F464} "}
              {p.name || p.identity}
              {p.identity === localParticipant.identity ? " (you)" : ""}
            </li>
          ))}
        </ul>
      </div>

      <Link
        href="/"
        style={{
          color: "#6366f1",
          fontSize: "0.85rem",
          textDecoration: "underline",
        }}
      >
        Back to main app
      </Link>
    </div>
  );
}

export default function TestPage() {
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

  if (connectionDetails) {
    return (
      <div style={{ height: "100vh", background: "#0f172a" }}>
        <LiveKitRoom
          token={connectionDetails.token}
          serverUrl={connectionDetails.url}
          connect={true}
          audio={{
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
          }}
          style={{ height: "100%" }}
        >
          <AudioTest />
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
      <h1 style={{ fontSize: "2rem", fontWeight: "bold" }}>Audio Test</h1>
      <p style={{ color: "#94a3b8" }}>
        Test your microphone through LiveKit (no agent needed)
      </p>
      <button
        onClick={connect}
        disabled={connecting}
        style={{
          padding: "0.8rem 2rem",
          borderRadius: "10px",
          border: "none",
          background: connecting ? "#475569" : "#22c55e",
          color: "white",
          fontSize: "1rem",
          cursor: connecting ? "default" : "pointer",
          fontWeight: "bold",
        }}
      >
        {connecting ? "Connecting..." : "Test Microphone"}
      </button>
    </div>
  );
}
