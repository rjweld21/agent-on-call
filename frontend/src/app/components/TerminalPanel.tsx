"use client";

import { useState, useEffect, useRef } from "react";

export interface TerminalEntry {
  id: string;
  timestamp: Date;
  command: string;
  output: string;
  exitCode: number;
  status: "running" | "completed" | "failed";
}

interface TerminalPanelProps {
  entries: TerminalEntry[];
}

export function TerminalPanel({ entries }: TerminalPanelProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new entries arrive
  useEffect(() => {
    if (scrollRef.current && !isCollapsed) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [entries.length, isCollapsed]);

  const completedCount = entries.filter(
    (e) => e.status === "completed" || e.status === "failed"
  ).length;
  const runningCount = entries.filter((e) => e.status === "running").length;

  return (
    <div
      data-testid="terminal-panel"
      style={{
        width: "100%",
        border: "1px solid #30363d",
        borderRadius: "0",
        background: "#0d1117",
        overflow: "hidden",
        fontFamily:
          'Menlo, Monaco, Consolas, "Courier New", monospace',
        display: "flex",
        flexDirection: "column" as const,
        flex: 1,
        minHeight: 0,
      }}
    >
      {/* Header */}
      <button
        data-testid="terminal-panel-toggle"
        onClick={() => setIsCollapsed(!isCollapsed)}
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          width: "100%",
          padding: "0.5rem 0.8rem",
          background: "#161b22",
          border: "none",
          borderBottom: isCollapsed ? "none" : "1px solid #30363d",
          color: "#c9d1d9",
          cursor: "pointer",
          fontSize: "0.8rem",
          fontWeight: 600,
          textAlign: "left",
          fontFamily:
            'Menlo, Monaco, Consolas, "Courier New", monospace',
        }}
      >
        <span>
          Terminal Output
          {entries.length > 0 && (
            <span
              data-testid="terminal-entry-count"
              style={{
                marginLeft: "0.5rem",
                color: "#8b949e",
                fontSize: "0.7rem",
                fontWeight: 400,
              }}
            >
              ({completedCount}/{entries.length})
            </span>
          )}
          {runningCount > 0 && (
            <span
              data-testid="terminal-running-indicator"
              style={{
                marginLeft: "0.5rem",
                color: "#f59e0b",
                fontSize: "0.7rem",
                fontWeight: 400,
              }}
            >
              running...
            </span>
          )}
        </span>
        <span
          style={{
            transform: isCollapsed ? "rotate(-90deg)" : "rotate(0deg)",
            transition: "transform 0.15s",
            fontSize: "0.7rem",
          }}
        >
          &#9660;
        </span>
      </button>

      {/* Content */}
      {!isCollapsed && (
        <div
          ref={scrollRef}
          data-testid="terminal-panel-content"
          style={{
            flex: 1,
            minHeight: 0,
            overflowY: "auto",
            padding: "0.5rem 0",
          }}
        >
          {entries.length === 0 ? (
            <p
              data-testid="terminal-empty"
              style={{
                color: "#484f58",
                fontSize: "0.75rem",
                fontStyle: "italic",
                margin: 0,
                padding: "0.5rem 0.8rem",
              }}
            >
              No commands executed yet...
            </p>
          ) : (
            entries.map((entry) => (
              <div
                key={entry.id}
                data-testid="terminal-entry"
                style={{
                  padding: "0.4rem 0.8rem",
                  borderBottom: "1px solid #21262d",
                }}
              >
                {/* Command line */}
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "0.3rem",
                  }}
                >
                  <span
                    data-testid="terminal-prompt"
                    style={{ color: "#3fb950", fontWeight: 700 }}
                  >
                    $
                  </span>
                  <span
                    data-testid="terminal-command"
                    style={{
                      color: "#c9d1d9",
                      fontSize: "0.8rem",
                      flex: 1,
                    }}
                  >
                    {entry.command}
                  </span>
                  {/* Exit code badge */}
                  {entry.status !== "running" && (
                    <span
                      data-testid="terminal-exit-code"
                      style={{
                        fontSize: "0.65rem",
                        fontWeight: 600,
                        padding: "0.1rem 0.3rem",
                        borderRadius: "4px",
                        background:
                          entry.exitCode === 0
                            ? "rgba(63, 185, 80, 0.15)"
                            : "rgba(248, 81, 73, 0.15)",
                        color:
                          entry.exitCode === 0 ? "#3fb950" : "#f85149",
                        flexShrink: 0,
                      }}
                    >
                      {entry.exitCode === 0 ? "\u2713 0" : `\u2717 ${entry.exitCode}`}
                    </span>
                  )}
                  {entry.status === "running" && (
                    <span
                      data-testid="terminal-running-badge"
                      style={{
                        fontSize: "0.65rem",
                        color: "#f59e0b",
                        flexShrink: 0,
                      }}
                    >
                      &#9679;
                    </span>
                  )}
                </div>

                {/* Output */}
                {entry.output && entry.status !== "running" && (
                  <pre
                    data-testid="terminal-output"
                    style={{
                      color: "#8b949e",
                      fontSize: "0.7rem",
                      margin: "0.3rem 0 0 1.1rem",
                      whiteSpace: "pre-wrap",
                      wordBreak: "break-word",
                      lineHeight: 1.4,
                      maxHeight: "150px",
                      overflow: "auto",
                    }}
                  >
                    {entry.output}
                  </pre>
                )}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
