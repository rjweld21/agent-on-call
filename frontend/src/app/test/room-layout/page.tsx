"use client";

import { useState } from "react";
import { SettingsProvider } from "@/lib/settings-context";
import { SettingsPanel } from "@/app/components/SettingsPanel";
import { ThinkingPanel, type ActivityItem } from "@/app/components/ThinkingPanel";
import { TerminalPanel, type TerminalEntry } from "@/app/components/TerminalPanel";
import {
  formatLocalTime,
  groupTranscriptEntries,
  detectGap,
  type TranscriptEntry,
} from "@/lib/transcript-time";

/**
 * Test page for 3-column room layout E2E testing.
 * Renders the room layout with mock data, no LiveKit required.
 */

const MOCK_TRANSCRIPT: TranscriptEntry[] = [
  { id: "user-1", speaker: "user", text: "Hello agent, can you help me?", timestamp: new Date("2026-01-01T00:00:00") },
  { id: "agent-1", speaker: "agent", text: "Of course! How can I assist you today?", timestamp: new Date("2026-01-01T00:00:02") },
  { id: "user-2", speaker: "user", text: "Please check the server status.", timestamp: new Date("2026-01-01T00:00:10") },
  { id: "agent-2", speaker: "agent", text: "Let me check that for you now.", timestamp: new Date("2026-01-01T00:00:12") },
];

const MOCK_ACTIVITIES: ActivityItem[] = [
  { id: "a1", type: "thinking", text: "Analyzing request...", timestamp: new Date("2026-01-01T00:00:12") },
  { id: "a2", type: "tool_call", text: "check_server_status", timestamp: new Date("2026-01-01T00:00:13"), tool: "exec_command", status: "started" },
  { id: "a3", type: "executing", text: "Running: curl http://server/health", timestamp: new Date("2026-01-01T00:00:14"), tool: "exec_command", status: "completed" },
];

const MOCK_TERMINAL: TerminalEntry[] = [
  { id: "t1", timestamp: new Date("2026-01-01T00:00:14"), command: "curl http://server/health", output: '{"status": "healthy", "uptime": "72h"}', exitCode: 0, status: "completed" },
  { id: "t2", timestamp: new Date("2026-01-01T00:00:16"), command: "df -h /", output: "Filesystem  Size  Used  Avail  Use%  Mounted on\n/dev/sda1   50G   22G   26G    46%  /", exitCode: 0, status: "completed" },
];

export default function RoomLayoutTestPage() {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const transcript = MOCK_TRANSCRIPT;

  return (
    <SettingsProvider>
      <div style={{ height: "100vh", background: "#0f172a" }}>
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
          {/* LEFT COLUMN: Transcript */}
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
              style={{
                flex: 1,
                overflowY: "auto",
                padding: "0.8rem",
                background: "#1e293b",
              }}
            >
              {(() => {
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
                          color: group.speaker === "agent" ? "#fcd34d" : "#60a5fa",
                          fontWeight: "bold", marginRight: "0.5rem",
                        }}>
                          {group.speaker === "agent" ? "Agent:" : "You:"}
                        </span>
                        <span style={{ color: "#cbd5e1" }}>{group.text}</span>
                      </div>
                    </div>
                  );
                });
              })()}
            </div>

            {/* Text input */}
            <div style={{
              display: "flex",
              borderTop: "1px solid #334155",
              background: "#0f172a",
              flexShrink: 0,
            }}>
              <input
                type="text"
                placeholder="Type a message, paste a URL..."
                style={{
                  flex: 1, padding: "0.6rem 0.8rem",
                  background: "transparent", border: "none", outline: "none",
                  color: "#e2e8f0", fontSize: "0.85rem",
                }}
              />
              <button style={{
                padding: "0.6rem 1rem",
                background: "#1e293b",
                border: "none", color: "#475569",
                fontSize: "0.85rem", fontWeight: "bold",
              }}>
                Send
              </button>
            </div>
          </div>

          {/* CENTER COLUMN: Controls */}
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

            {/* Participants */}
            <div style={{ width: "100%" }}>
              <h3 style={{ fontSize: "0.85rem", color: "#94a3b8", marginBottom: "0.4rem" }}>
                Participants (2)
              </h3>
              <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
                <li style={{ padding: "0.2rem 0.6rem", fontSize: "0.85rem", color: "#e2e8f0" }}>
                  You
                </li>
                <li style={{ padding: "0.2rem 0.6rem", fontSize: "0.85rem", color: "#fcd34d" }}>
                  Agent
                </li>
              </ul>
            </div>

            <p style={{ color: "#94a3b8", margin: 0 }}>
              Agent Status: <span style={{ color: "#3b82f6", fontWeight: "bold" }}>listening</span>
            </p>

            {/* Placeholder for BarVisualizer */}
            <div style={{
              width: "100%", maxWidth: "300px", height: "60px",
              background: "#1e293b", borderRadius: "8px",
              display: "flex", alignItems: "center", justifyContent: "center",
              color: "#475569", fontSize: "0.75rem",
            }}>
              [Audio Visualizer]
            </div>

            {/* Placeholder for MicMonitor */}
            <div style={{ width: "100%", maxWidth: "500px" }}>
              <h3 style={{ fontSize: "0.85rem", color: "#94a3b8", marginBottom: "0.4rem" }}>
                Microphone <span style={{ color: "#22c55e" }}>Active</span>
              </h3>
              <div style={{
                width: "100%", height: "20px", background: "#0f172a",
                borderRadius: "6px", border: "1px solid #334155",
              }} />
            </div>

            {/* Call Controls */}
            <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginTop: "auto", paddingTop: "1rem" }}>
              <button style={{
                width: "48px", height: "48px", borderRadius: "50%",
                border: "2px solid #22c55e", background: "transparent",
                color: "#e2e8f0", cursor: "pointer", fontSize: "1.3rem",
              }}>
                Mute
              </button>
              <button style={{
                padding: "0.5rem 1.5rem", borderRadius: "8px",
                border: "1px solid #dc2626", background: "#7f1d1d",
                color: "#fca5a5", cursor: "pointer", fontSize: "0.9rem",
              }}>
                Leave Call
              </button>
            </div>
          </div>

          {/* RIGHT COLUMN: Activity + Terminal */}
          <div
            data-testid="column-activity"
            style={{
              display: "flex",
              flexDirection: "column",
              height: "100%",
              overflow: "hidden",
            }}
          >
            <div style={{ flex: 1, minHeight: 0, overflow: "hidden", display: "flex", flexDirection: "column" }}>
              <ThinkingPanel activities={MOCK_ACTIVITIES} isAgentWorking={false} />
            </div>
            <div style={{ flex: 1, minHeight: 0, overflow: "hidden", display: "flex", flexDirection: "column", borderTop: "1px solid #334155" }}>
              <TerminalPanel entries={MOCK_TERMINAL} onClear={() => {}} />
            </div>
          </div>

          <SettingsPanel isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />
        </div>
      </div>
    </SettingsProvider>
  );
}
