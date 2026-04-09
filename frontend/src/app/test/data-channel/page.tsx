"use client";

import { useState, useCallback } from "react";
import { SettingsProvider } from "@/lib/settings-context";
import { ThinkingPanel, type ActivityItem } from "@/app/components/ThinkingPanel";
import { TerminalPanel, type TerminalEntry } from "@/app/components/TerminalPanel";

/**
 * Test page for data channel message handling E2E tests.
 *
 * Simulates the data channel message processing logic from page.tsx
 * without requiring a LiveKit connection. Buttons trigger simulated
 * messages that go through the same state update paths.
 */

interface TtsBanner {
  reason: string;
}

export default function DataChannelTestPage() {
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [terminalEntries, setTerminalEntries] = useState<TerminalEntry[]>([]);
  const [ttsBanner, setTtsBanner] = useState<TtsBanner | null>(null);
  const [lastError, setLastError] = useState<string | null>(null);

  /**
   * Process a simulated data channel message using the same logic
   * as the real handleDataReceived in page.tsx.
   */
  const processMessage = useCallback((payload: Uint8Array) => {
    try {
      const text = new TextDecoder().decode(payload);
      const msg = JSON.parse(text);

      if (msg?.type === "tts_status") {
        if (msg.available === false && msg.reason) {
          setTtsBanner({ reason: msg.reason });
        } else if (msg.available === true) {
          setTtsBanner(null);
        }
      }

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
          const existingIdx = prev.findIndex((a) => a.id === action.id);
          if (existingIdx >= 0) {
            const updated = [...prev];
            updated[existingIdx] = { ...updated[existingIdx], ...newItem };
            return updated;
          }
          return [...prev, newItem];
        });

        const commandTools = new Set([
          "exec_command", "git_clone", "git_commit", "git_push", "git_status",
          "web_fetch", "web_search",
        ]);
        if (commandTools.has(action.tool)) {
          setTerminalEntries((prev) => {
            const existingIdx = prev.findIndex((e) => e.id === action.id);
            if (action.status === "started" || (action.kind === "executing" && existingIdx < 0)) {
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

      if (msg?.type === "command_output") {
        setTerminalEntries((prev) => {
          const existingIdx = prev.findIndex((e) => e.id === msg.id);
          if (existingIdx >= 0) {
            const updated = [...prev];
            updated[existingIdx] = {
              ...updated[existingIdx],
              command: msg.command || updated[existingIdx].command,
              output: msg.output || "",
              exitCode: msg.exitCode ?? 0,
              status: msg.done
                ? (msg.exitCode === 0 ? "completed" : "failed")
                : "running",
              tool: msg.tool || updated[existingIdx].tool,
            };
            return updated;
          }
          return [...prev, {
            id: msg.id,
            timestamp: msg.timestamp ? new Date(msg.timestamp) : new Date(),
            command: msg.command || "command",
            output: msg.output || "",
            exitCode: msg.exitCode ?? 0,
            status: msg.done
              ? (msg.exitCode === 0 ? "completed" as const : "failed" as const)
              : "running" as const,
            tool: msg.tool || "",
          }];
        });
      }

      setLastError(null);
    } catch {
      // Same as real handler: silently ignore non-JSON
      setLastError(null);
    }
  }, []);

  /** Helper to send a simulated message */
  const send = useCallback((data: unknown) => {
    const encoded = new TextEncoder().encode(JSON.stringify(data));
    processMessage(encoded);
  }, [processMessage]);

  /** Send a raw Uint8Array (for malformed message testing) */
  const sendRaw = useCallback((raw: Uint8Array) => {
    processMessage(raw);
  }, [processMessage]);

  // --- Trigger buttons for E2E tests ---

  const sendAgentAction = useCallback(() => {
    send({
      type: "agent_action",
      action: {
        id: `action-${Date.now()}`,
        kind: "thinking",
        summary: "Analyzing the user request...",
        timestamp: new Date().toISOString(),
        status: "started",
      },
    });
  }, [send]);

  const sendCommandOutput = useCallback(() => {
    const id = `cmd-${Date.now()}`;
    // First send started action
    send({
      type: "agent_action",
      action: {
        id,
        kind: "executing",
        summary: "Running: ls -la /tmp",
        timestamp: new Date().toISOString(),
        tool: "exec_command",
        status: "started",
      },
    });
    // Then send command_output with result
    setTimeout(() => {
      send({
        type: "command_output",
        id,
        command: "ls -la /tmp",
        output: "total 0\ndrwxrwxrwt 2 root root 40 Jan  1 00:00 .\ndrwxr-xr-x 1 root root 40 Jan  1 00:00 ..",
        exitCode: 0,
        done: true,
        tool: "exec_command",
      });
    }, 100);
  }, [send]);

  const sendTtsUnavailable = useCallback(() => {
    send({
      type: "tts_status",
      available: false,
      reason: "TTS service quota exceeded",
    });
  }, [send]);

  const sendTtsAvailable = useCallback(() => {
    send({
      type: "tts_status",
      available: true,
    });
  }, [send]);

  const sendMalformed = useCallback(() => {
    // Send invalid bytes that aren't valid JSON
    sendRaw(new Uint8Array([0xFF, 0xFE, 0x00, 0x01]));
    // Track that we tried (the handler should not crash)
    setLastError("malformed_sent");
  }, [sendRaw]);

  const sendSettingsUpdate = useCallback(() => {
    send({
      type: "settings_update",
      settings: { verbosity: "detailed", model: "gpt-4" },
    });
  }, [send]);

  return (
    <SettingsProvider>
      <div
        data-testid="data-channel-test-page"
        style={{
          display: "grid",
          gridTemplateColumns: "300px 1fr",
          height: "100vh",
          background: "#0f172a",
          fontFamily: "system-ui, sans-serif",
          color: "#e2e8f0",
        }}
      >
        {/* Control panel — left side */}
        <div
          data-testid="control-panel"
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "0.5rem",
            padding: "1rem",
            borderRight: "1px solid #334155",
            overflowY: "auto",
          }}
        >
          <h2 style={{ fontSize: "1rem", margin: 0 }}>
            Data Channel Test
          </h2>
          <p style={{ fontSize: "0.75rem", color: "#94a3b8", margin: 0 }}>
            Simulate data channel messages without LiveKit.
          </p>

          <hr style={{ borderColor: "#334155", margin: "0.5rem 0" }} />

          <button
            data-testid="btn-agent-action"
            onClick={sendAgentAction}
            style={btnStyle}
          >
            Send agent_action (thinking)
          </button>

          <button
            data-testid="btn-command-output"
            onClick={sendCommandOutput}
            style={btnStyle}
          >
            Send command_output (exec_command)
          </button>

          <button
            data-testid="btn-tts-unavailable"
            onClick={sendTtsUnavailable}
            style={btnStyle}
          >
            Send tts_status (unavailable)
          </button>

          <button
            data-testid="btn-tts-available"
            onClick={sendTtsAvailable}
            style={btnStyle}
          >
            Send tts_status (available)
          </button>

          <button
            data-testid="btn-malformed"
            onClick={sendMalformed}
            style={btnStyle}
          >
            Send malformed message
          </button>

          <button
            data-testid="btn-settings-update"
            onClick={sendSettingsUpdate}
            style={btnStyle}
          >
            Send settings_update
          </button>

          <hr style={{ borderColor: "#334155", margin: "0.5rem 0" }} />

          {/* Status indicators for E2E assertions */}
          <div data-testid="status-panel" style={{ fontSize: "0.75rem" }}>
            <div>
              Activities: <span data-testid="activity-count">{activities.length}</span>
            </div>
            <div>
              Terminal entries: <span data-testid="terminal-count">{terminalEntries.length}</span>
            </div>
            <div>
              TTS banner:{" "}
              <span data-testid="tts-status">
                {ttsBanner ? `unavailable: ${ttsBanner.reason}` : "none"}
              </span>
            </div>
            {lastError === "malformed_sent" && (
              <div data-testid="malformed-handled" style={{ color: "#22c55e" }}>
                Malformed message processed (no crash)
              </div>
            )}
          </div>
        </div>

        {/* Display panels — right side */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            height: "100%",
            overflow: "hidden",
          }}
        >
          {/* TTS banner */}
          {ttsBanner && (
            <div
              data-testid="tts-banner"
              style={{
                padding: "0.5rem 1rem",
                background: "#7f1d1d",
                color: "#fca5a5",
                fontSize: "0.8rem",
                flexShrink: 0,
              }}
            >
              TTS unavailable: {ttsBanner.reason}
            </div>
          )}

          {/* ThinkingPanel */}
          <div style={{ flex: 1, minHeight: 0, overflow: "hidden", display: "flex", flexDirection: "column" }}>
            <ThinkingPanel activities={activities} isAgentWorking={activities.length > 0} />
          </div>

          {/* TerminalPanel */}
          <div style={{ flex: 1, minHeight: 0, overflow: "hidden", display: "flex", flexDirection: "column", borderTop: "1px solid #334155" }}>
            <TerminalPanel entries={terminalEntries} onClear={() => setTerminalEntries([])} />
          </div>
        </div>
      </div>
    </SettingsProvider>
  );
}

const btnStyle: React.CSSProperties = {
  padding: "0.4rem 0.8rem",
  borderRadius: "6px",
  border: "1px solid #334155",
  background: "#1e293b",
  color: "#e2e8f0",
  cursor: "pointer",
  fontSize: "0.75rem",
  textAlign: "left",
};
