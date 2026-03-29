"use client";

import {
  LiveKitRoom,
  RoomAudioRenderer,
  useVoiceAssistant,
  BarVisualizer,
  DisconnectButton,
  useParticipants,
  useLocalParticipant,
  useTrackTranscription,
  useChat,
  useRoomContext,
} from "@livekit/components-react";
import { Track, RemoteParticipant } from "livekit-client";
import "@livekit/components-styles";
import { useCallback, useState, useEffect, useRef, KeyboardEvent } from "react";
import {
  formatLocalTime,
  detectGap,
  groupTranscriptEntries,
  type TranscriptEntry,
} from "@/lib/transcript-time";
import { SettingsProvider, useSettings, useSettingsSync } from "@/lib/settings-context";
import { SettingsPanel } from "@/app/components/SettingsPanel";
import { ThinkingPanel, type ActivityItem } from "@/app/components/ThinkingPanel";
import { TerminalPanel, type TerminalEntry } from "@/app/components/TerminalPanel";
import { MuteButton } from "@/app/components/MuteButton";

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
  const { state, audioTrack } = useVoiceAssistant();
  const { agentTranscriptions } = useVoiceAssistant();
  const participants = useParticipants();
  const { localParticipant, microphoneTrack } = useLocalParticipant();
  const room = useRoomContext();
  const transcriptRef = useRef<HTMLDivElement>(null);
  const [textInput, setTextInput] = useState("");
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [ttsBanner, setTtsBanner] = useState<{ reason: string } | null>(null);
  const [systemMessages, setSystemMessages] = useState<TranscriptEntry[]>([]);
  const [terminalEntries, setTerminalEntries] = useState<TerminalEntry[]>([]);

  // Sync settings changes to agent via data channel
  useSettingsSync(room);

  // Listen for TTS status messages from the agent
  useEffect(() => {
    const handleDataReceived = (payload: unknown) => {
      try {
        // LiveKit data packet — extract data bytes
        const packet = payload as { data?: Uint8Array };
        if (!packet?.data) return;
        const text = new TextDecoder().decode(packet.data);
        const msg = JSON.parse(text);
        if (msg?.type === "tts_status") {
          if (msg.available === false && msg.reason) {
            setTtsBanner({ reason: msg.reason });
          } else if (msg.available === true) {
            setTtsBanner(null);
          }
        }
        // Handle agent action events for the activity panel
        if (msg?.type === "agent_action" && msg.action) {
          const action = msg.action;
          const newItem: ActivityItem = {
            id: action.id,
            type: action.kind as ActivityItem["type"],
            text: action.summary,
            timestamp: new Date(action.timestamp || Date.now()),
            detail: action.detail || undefined,
            tool: action.tool,
            status: action.status,
          };
          setActivities((prev) => {
            // If action with same ID exists, update it in-place (status change)
            const existingIdx = prev.findIndex((a) => a.id === action.id);
            if (existingIdx >= 0) {
              const updated = [...prev];
              updated[existingIdx] = { ...updated[existingIdx], ...newItem };
              return updated;
            }
            return [...prev, newItem];
          });

          // Build terminal entries from command tool actions
          const commandTools = new Set([
            "exec_command", "git_clone", "git_commit", "git_push", "git_status",
            "web_fetch", "web_search",
          ]);
          if (commandTools.has(action.tool)) {
            setTerminalEntries((prev) => {
              const existingIdx = prev.findIndex((e) => e.id === action.id);
              if (action.status === "started" || (action.kind === "executing" && existingIdx < 0)) {
                // Extract command from summary (e.g. "Running: ls -la")
                const cmdMatch = (action.summary || "").match(/^(?:Running|Cloning|Committing|Pushing|Checking):\s*(.+)/);
                const command = cmdMatch ? cmdMatch[1] : action.detail || action.summary || action.tool;
                if (existingIdx >= 0) {
                  const updated = [...prev];
                  updated[existingIdx] = { ...updated[existingIdx], status: "running" };
                  return updated;
                }
                return [...prev, {
                  id: action.id,
                  timestamp: new Date(action.timestamp || Date.now()),
                  command,
                  output: "",
                  exitCode: 0,
                  status: "running" as const,
                }];
              }
              if (action.status === "completed" || action.status === "failed") {
                // Parse exit code from detail or summary
                const exitMatch = (action.detail || action.summary || "").match(/exit (?:code:?\s*)?(\d+)/i);
                const exitCode = exitMatch ? parseInt(exitMatch[1], 10) : (action.status === "failed" ? 1 : 0);
                const output = action.detail || action.summary || "";
                if (existingIdx >= 0) {
                  const updated = [...prev];
                  updated[existingIdx] = {
                    ...updated[existingIdx],
                    output,
                    exitCode,
                    status: action.status === "failed" ? "failed" : "completed",
                  };
                  return updated;
                }
                // No matching started entry — create completed entry directly
                return [...prev, {
                  id: action.id,
                  timestamp: new Date(action.timestamp || Date.now()),
                  command: action.tool,
                  output,
                  exitCode,
                  status: action.status === "failed" ? "failed" as const : "completed" as const,
                }];
              }
              return prev;
            });
          }
        }
        // Handle command_output messages for full terminal output streaming
        if (msg?.type === "command_output") {
          setTerminalEntries((prev) => {
            const existingIdx = prev.findIndex((e) => e.id === msg.id);
            if (existingIdx >= 0) {
              const updated = [...prev];
              updated[existingIdx] = {
                ...updated[existingIdx],
                output: msg.output || "",
                exitCode: msg.exitCode ?? 0,
                status: msg.done
                  ? (msg.exitCode === 0 ? "completed" : "failed")
                  : "running",
              };
              return updated;
            }
            // No matching entry yet — create one
            return [...prev, {
              id: msg.id,
              timestamp: new Date(),
              command: msg.command || "command",
              output: msg.output || "",
              exitCode: msg.exitCode ?? 0,
              status: msg.done
                ? (msg.exitCode === 0 ? "completed" as const : "failed" as const)
                : "running" as const,
            }];
          });
        }
      } catch {
        // Ignore non-JSON or unrelated messages
      }
    };
    room.on("dataReceived", handleDataReceived);
    return () => {
      room.off("dataReceived", handleDataReceived);
    };
  }, [room]);

  // Listen for agent join/leave events
  useEffect(() => {
    const handleParticipantConnected = (participant: RemoteParticipant) => {
      if (!participant.isAgent) return;
      const now = new Date();
      const id = `system-join-${participant.identity}-${now.getTime()}`;
      setSystemMessages((prev) => [
        ...prev,
        {
          id,
          speaker: "system" as const,
          text: "[Agent joined the call]",
          timestamp: now,
        },
      ]);
      setActivities((prev) => [
        ...prev,
        {
          id,
          type: "system" as const,
          text: "Agent joined the call",
          timestamp: now,
        },
      ]);
    };

    const handleParticipantDisconnected = (participant: RemoteParticipant) => {
      if (!participant.isAgent) return;
      const now = new Date();
      const id = `system-leave-${participant.identity}-${now.getTime()}`;
      setSystemMessages((prev) => [
        ...prev,
        {
          id,
          speaker: "system" as const,
          text: "[Agent left the call]",
          timestamp: now,
        },
      ]);
      setActivities((prev) => [
        ...prev,
        {
          id,
          type: "system" as const,
          text: "Agent left the call",
          timestamp: now,
        },
      ]);
    };

    room.on("participantConnected", handleParticipantConnected);
    room.on("participantDisconnected", handleParticipantDisconnected);
    return () => {
      room.off("participantConnected", handleParticipantConnected);
      room.off("participantDisconnected", handleParticipantDisconnected);
    };
  }, [room]);

  // Build a TrackReferenceOrPlaceholder for the local mic so useTrackTranscription works
  const micTrackRef = microphoneTrack
    ? { participant: localParticipant, publication: microphoneTrack, source: Track.Source.Microphone }
    : { participant: localParticipant, source: Track.Source.Microphone };

  const { segments: userSegments } = useTrackTranscription(micTrackRef);
  const { chatMessages, send, isSending } = useChat();

  // Build a unified, time-sorted transcript from agent transcriptions,
  // user voice transcriptions, and chat messages. Only show final segments.
  const transcript: TranscriptEntry[] = [
    ...agentTranscriptions
      .filter((seg) => seg.final)
      .map((seg) => ({
        id: `agent-${seg.id}`,
        speaker: "agent" as const,
        text: seg.text,
        timestamp: new Date(seg.firstReceivedTime ?? 0),
      })),
    ...userSegments
      .filter((seg) => seg.final)
      .map((seg) => ({
        id: `user-${seg.id}`,
        speaker: "user" as const,
        text: seg.text,
        timestamp: new Date(seg.firstReceivedTime ?? 0),
      })),
    ...chatMessages.map((msg) => ({
      id: `chat-${msg.timestamp}`,
      speaker: "user-text" as const,
      text: msg.message,
      timestamp: new Date(msg.timestamp),
    })),
    ...systemMessages,
  ].sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());

  // Auto-scroll transcript to bottom whenever entries change
  useEffect(() => {
    if (transcriptRef.current) {
      transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
    }
  }, [transcript.length]);

  const sendMessage = useCallback(async () => {
    const msg = textInput.trim();
    if (!msg || isSending) return;
    setTextInput("");
    await send(msg);
  }, [textInput, isSending, send]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Enter") {
        sendMessage();
      }
    },
    [sendMessage],
  );

  return (
    <div
      data-testid="room-layout"
      style={{
        display: "grid",
        gridTemplateColumns: "minmax(0, 27%) minmax(0, 38%) minmax(0, 35%)",
        height: "100%",
        fontFamily: "system-ui, sans-serif",
        color: "#e2e8f0",
        overflow: "hidden",
      }}
    >
      {/* ===== LEFT COLUMN: Transcript (full height, scrollable) ===== */}
      <div
        data-testid="column-transcript"
        style={{
          display: "flex",
          flexDirection: "column",
          height: "100%",
          borderRight: "1px solid #334155",
          overflow: "hidden",
        }}
      >
        <div style={{
          padding: "0.8rem",
          borderBottom: "1px solid #334155",
          flexShrink: 0,
        }}>
          <h3 style={{ fontSize: "0.85rem", color: "#94a3b8", margin: 0 }}>
            Transcript
          </h3>
        </div>
        <div
          ref={transcriptRef}
          style={{
            flex: 1,
            overflowY: "auto",
            padding: "0.8rem",
            background: "#1e293b",
          }}
        >
          {transcript.length === 0 ? (
            <p style={{ color: "#475569", fontSize: "0.8rem", fontStyle: "italic", margin: 0 }}>
              Speak or type to start the conversation...
            </p>
          ) : (
            (() => {
              const grouped = groupTranscriptEntries(transcript);
              return grouped.map((group, i) => {
                const gapText = i > 0 ? detectGap(grouped[i - 1].lastTimestamp, group.timestamp) : null;
                return (
                  <div key={group.ids.join("-")}>
                    {gapText && (
                      <div data-testid="gap-indicator" style={{
                        textAlign: "center", color: "#64748b", fontSize: "0.7rem",
                        fontStyle: "italic", padding: "0.2rem 0",
                      }}>
                        --- {gapText} ---
                      </div>
                    )}
                    {group.speaker === "system" ? (
                      <div
                        data-testid="system-message"
                        style={{
                          padding: "0.3rem 0", fontSize: "0.75rem",
                          borderBottom: i < grouped.length - 1 ? "1px solid #334155" : "none",
                          textAlign: "center",
                          fontStyle: "italic",
                          color: "#64748b",
                        }}
                      >
                        <span data-testid="transcript-timestamp" style={{
                          color: "#475569", fontSize: "0.7rem", marginRight: "0.5rem",
                          fontFamily: "monospace",
                        }}>
                          {formatLocalTime(group.timestamp)}
                        </span>
                        {group.text}
                      </div>
                    ) : (
                    <div style={{
                      padding: "0.3rem 0", fontSize: "0.85rem",
                      borderBottom: i < grouped.length - 1 ? "1px solid #334155" : "none",
                    }}>
                      <span data-testid="transcript-timestamp" style={{
                        color: "#475569", fontSize: "0.7rem", marginRight: "0.5rem",
                        fontFamily: "monospace",
                      }}>
                        {formatLocalTime(group.timestamp)}
                      </span>
                      <span style={{
                        color: group.speaker === "agent" ? "#fcd34d"
                          : group.speaker === "user-text" ? "#a78bfa"
                          : "#60a5fa",
                        fontWeight: "bold", marginRight: "0.5rem",
                      }}>
                        {group.speaker === "agent" ? "Agent:"
                          : group.speaker === "user-text" ? "You (text):"
                          : "You:"}
                      </span>
                      <span style={{ color: "#cbd5e1" }}>{group.text}</span>
                    </div>
                    )}
                  </div>
                );
              });
            })()
          )}
        </div>

        {/* Text input at bottom of transcript column */}
        <div style={{
          display: "flex",
          border: "none", borderTop: "1px solid #334155",
          overflow: "hidden",
          background: "#0f172a",
          flexShrink: 0,
        }}>
          <input
            type="text"
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a message, paste a URL..."
            style={{
              flex: 1, padding: "0.6rem 0.8rem",
              background: "transparent", border: "none", outline: "none",
              color: "#e2e8f0", fontSize: "0.85rem",
            }}
          />
          <button
            onClick={sendMessage}
            disabled={isSending || !textInput.trim()}
            style={{
              padding: "0.6rem 1rem",
              background: isSending || !textInput.trim() ? "#1e293b" : "#4f46e5",
              border: "none", color: isSending || !textInput.trim() ? "#475569" : "#e2e8f0",
              cursor: isSending || !textInput.trim() ? "default" : "pointer",
              fontSize: "0.85rem", fontWeight: "bold",
              transition: "background 0.15s",
            }}
          >
            Send
          </button>
        </div>
      </div>

      {/* ===== CENTER COLUMN: Controls ===== */}
      <div
        data-testid="column-controls"
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          height: "100%",
          overflowY: "auto",
          padding: "1.5rem 1rem",
          gap: "1.2rem",
          borderRight: "1px solid #334155",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <h1 style={{ fontSize: "1.5rem", fontWeight: "bold", margin: 0 }}>Agent On Call</h1>
          <button
            data-testid="settings-button"
            onClick={() => setSettingsOpen(true)}
            aria-label="Open settings"
            style={{
              background: "none",
              border: "1px solid #334155",
              borderRadius: "8px",
              color: "#94a3b8",
              cursor: "pointer",
              fontSize: "1.2rem",
              padding: "0.3rem 0.5rem",
              lineHeight: 1,
            }}
          >
            &#9881;
          </button>
        </div>

        {/* TTS unavailable banner */}
        {ttsBanner && (
          <div
            data-testid="tts-banner"
            style={{
              width: "100%",
              padding: "0.6rem 0.8rem",
              background: "rgba(245, 158, 11, 0.15)",
              border: "1px solid #f59e0b",
              borderRadius: "8px",
              color: "#fbbf24",
              fontSize: "0.8rem",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: "0.5rem",
            }}
          >
            <span>
              {ttsBanner.reason === "no_key"
                ? "Voice responses unavailable. Add a Cartesia API key in settings for voice responses."
                : ttsBanner.reason === "auth_failed"
                  ? "Voice responses unavailable. Cartesia API key is invalid."
                  : ttsBanner.reason === "no_credits"
                    ? "Voice responses unavailable. Cartesia account has no credits remaining."
                    : "Voice responses unavailable. Could not reach Cartesia API."}
            </span>
            <button
              data-testid="tts-banner-dismiss"
              onClick={() => setTtsBanner(null)}
              aria-label="Dismiss TTS notification"
              style={{
                background: "none",
                border: "none",
                color: "#fbbf24",
                cursor: "pointer",
                fontSize: "1rem",
                lineHeight: 1,
                padding: "0 0.2rem",
                flexShrink: 0,
              }}
            >
              &#10005;
            </button>
          </div>
        )}

        {/* Participants */}
        <div style={{ width: "100%" }}>
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
            {state === "speaking" && ttsBanner ? "responding" : state}
          </span>
        </p>

        <BarVisualizer
          state={state}
          barCount={5}
          trackRef={audioTrack}
          style={{ width: "100%", maxWidth: "300px", height: "60px" }}
        />

        {/* Mic Monitor */}
        <MicMonitor />

        {/* Call Controls */}
        <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginTop: "auto", paddingTop: "1rem" }}>
          <MuteButton />
          <DisconnectButton style={{
            padding: "0.5rem 1.5rem", borderRadius: "8px",
            border: "1px solid #dc2626", background: "#7f1d1d",
            color: "#fca5a5", cursor: "pointer", fontSize: "0.9rem",
          }}>
            Leave Call
          </DisconnectButton>
        </div>
      </div>

      {/* ===== RIGHT COLUMN: Activity (top 50%) + Terminal (bottom 50%) ===== */}
      <div
        data-testid="column-activity"
        style={{
          display: "flex",
          flexDirection: "column",
          height: "100%",
          overflow: "hidden",
        }}
      >
        {/* Agent Thinking/Activity Panel — top half */}
        <div style={{ flex: 1, minHeight: 0, overflow: "hidden", display: "flex", flexDirection: "column" }}>
          <ThinkingPanel
            activities={activities}
            isAgentWorking={state === "thinking"}
          />
        </div>

        {/* Terminal Output Panel — bottom half */}
        <div style={{ flex: 1, minHeight: 0, overflow: "hidden", display: "flex", flexDirection: "column", borderTop: "1px solid #334155" }}>
          <TerminalPanel entries={terminalEntries} />
        </div>
      </div>

      <SettingsPanel isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </div>
  );
}

function HomeInner() {
  const [connectionDetails, setConnectionDetails] = useState<{
    token: string;
    url: string;
  } | null>(null);
  const [connecting, setConnecting] = useState(false);
  const { settings } = useSettings();

  const connect = useCallback(async () => {
    setConnecting(true);
    try {
      const model = (settings.model?.anthropicModel as string) || "";
      const verbosity = (settings.voice?.verbosity as number) || 3;
      const params = new URLSearchParams();
      if (model) params.set("model", model);
      if (verbosity !== 3) params.set("verbosity", String(verbosity));
      const qs = params.toString();
      const resp = await fetch(`/api/token${qs ? `?${qs}` : ""}`);
      const data = await resp.json();
      setConnectionDetails({ token: data.token, url: data.url });
    } catch (err) {
      console.error("Failed to get token:", err);
    } finally {
      setConnecting(false);
    }
  }, [settings.model?.anthropicModel, settings.voice?.verbosity]);

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
          audio={{
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
          }}
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

export default function Home() {
  return (
    <SettingsProvider>
      <HomeInner />
    </SettingsProvider>
  );
}
