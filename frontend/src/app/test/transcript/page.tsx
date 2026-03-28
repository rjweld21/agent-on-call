"use client";

import { formatElapsedTime, detectGap, getSessionStartTime } from "@/lib/transcript-time";

/**
 * Test page that renders mock transcript entries for E2E testing.
 * Not used in production — only for verifying timestamp display.
 */

interface TranscriptEntry {
  id: string;
  speaker: "user" | "agent" | "user-text";
  text: string;
  timestamp: Date;
}

const baseTime = new Date("2026-01-15T10:00:00Z");

const mockTranscript: TranscriptEntry[] = [
  { id: "1", speaker: "user", text: "Hello, I need help with my project.", timestamp: new Date(baseTime.getTime()) },
  { id: "2", speaker: "agent", text: "Of course! What do you need?", timestamp: new Date(baseTime.getTime() + 5000) },
  { id: "3", speaker: "user", text: "Can you check the deployment status?", timestamp: new Date(baseTime.getTime() + 15000) },
  // 90-second gap here to trigger gap indicator
  { id: "4", speaker: "agent", text: "The deployment completed successfully.", timestamp: new Date(baseTime.getTime() + 105000) },
  { id: "5", speaker: "user-text", text: "Great, thanks!", timestamp: new Date(baseTime.getTime() + 110000) },
];

export default function TranscriptTestPage() {
  const sessionStart = getSessionStartTime(mockTranscript);

  return (
    <div style={{ background: "#0f172a", minHeight: "100vh", padding: "2rem", fontFamily: "system-ui, sans-serif", color: "#e2e8f0" }}>
      <h1>Transcript Timestamp Test</h1>
      <div data-testid="transcript-container" style={{
        maxWidth: "500px", border: "1px solid #334155", borderRadius: "8px",
        padding: "0.8rem", background: "#1e293b",
      }}>
        {mockTranscript.map((entry, i) => {
          const gapText = i > 0 ? detectGap(mockTranscript[i - 1].timestamp, entry.timestamp) : null;
          const elapsedMs = sessionStart ? entry.timestamp.getTime() - sessionStart.getTime() : 0;
          return (
            <div key={entry.id}>
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
                borderBottom: i < mockTranscript.length - 1 ? "1px solid #334155" : "none",
              }}>
                <span data-testid="transcript-timestamp" style={{
                  color: "#475569", fontSize: "0.7rem", marginRight: "0.5rem",
                  fontFamily: "monospace",
                }}>
                  {formatElapsedTime(elapsedMs)}
                </span>
                <span style={{
                  color: entry.speaker === "agent" ? "#fcd34d"
                    : entry.speaker === "user-text" ? "#a78bfa"
                    : "#60a5fa",
                  fontWeight: "bold", marginRight: "0.5rem",
                }}>
                  {entry.speaker === "agent" ? "Agent:"
                    : entry.speaker === "user-text" ? "You (text):"
                    : "You:"}
                </span>
                <span style={{ color: "#cbd5e1" }}>{entry.text}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
