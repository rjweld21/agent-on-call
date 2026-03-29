"use client";

import { useState, useEffect, useRef, useCallback } from "react";

export interface TerminalEntry {
  id: string;
  timestamp: Date;
  command: string;
  output: string;
  exitCode: number;
  status: "running" | "completed" | "failed";
  tool?: string;
}

type FilterMode = "all" | "commands" | "errors";

interface TerminalPanelProps {
  entries: TerminalEntry[];
  onClear?: () => void;
}

function formatTime(date: Date): string {
  const h = String(date.getHours()).padStart(2, "0");
  const m = String(date.getMinutes()).padStart(2, "0");
  const s = String(date.getSeconds()).padStart(2, "0");
  return `${h}:${m}:${s}`;
}

function countOutputLines(output: string): number {
  if (!output) return 0;
  return output.split("\n").length;
}

export function TerminalPanel({ entries, onClear }: TerminalPanelProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [filter, setFilter] = useState<FilterMode>("all");
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new entries arrive
  useEffect(() => {
    if (scrollRef.current && !isCollapsed) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [entries.length, isCollapsed]);

  const toggleExpand = useCallback((id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }, []);

  const copyCommand = useCallback(async (id: string, command: string) => {
    try {
      await navigator.clipboard.writeText(command);
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 1500);
    } catch {
      // Clipboard API may fail in some environments
    }
  }, []);

  const filteredEntries = entries.filter((entry) => {
    if (filter === "errors") return entry.status === "failed" || entry.exitCode !== 0;
    if (filter === "commands") return entry.status !== "running";
    return true;
  });

  const completedCount = entries.filter(
    (e) => e.status === "completed" || e.status === "failed"
  ).length;
  const runningCount = entries.filter((e) => e.status === "running").length;
  const errorCount = entries.filter(
    (e) => e.status === "failed" || (e.exitCode !== 0 && e.status !== "running")
  ).length;

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
        <>
          {/* Filter bar */}
          <div
            data-testid="terminal-filter-bar"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.4rem",
              padding: "0.3rem 0.8rem",
              background: "#161b22",
              borderBottom: "1px solid #30363d",
              fontSize: "0.7rem",
            }}
          >
            {(["all", "commands", "errors"] as FilterMode[]).map((mode) => (
              <button
                key={mode}
                data-testid={`terminal-filter-${mode}`}
                onClick={(e) => {
                  e.stopPropagation();
                  setFilter(mode);
                }}
                style={{
                  padding: "0.15rem 0.5rem",
                  borderRadius: "4px",
                  border: "1px solid",
                  borderColor: filter === mode ? "#58a6ff" : "#30363d",
                  background: filter === mode ? "rgba(88, 166, 255, 0.15)" : "transparent",
                  color: filter === mode ? "#58a6ff" : "#8b949e",
                  cursor: "pointer",
                  fontSize: "0.65rem",
                  fontFamily: 'Menlo, Monaco, Consolas, "Courier New", monospace',
                }}
              >
                {mode === "all" ? "All" : mode === "commands" ? "Commands" : `Errors (${errorCount})`}
              </button>
            ))}
            <div style={{ flex: 1 }} />
            <button
              data-testid="terminal-clear-button"
              onClick={(e) => {
                e.stopPropagation();
                onClear?.();
              }}
              style={{
                padding: "0.15rem 0.5rem",
                borderRadius: "4px",
                border: "1px solid #30363d",
                background: "transparent",
                color: "#8b949e",
                cursor: "pointer",
                fontSize: "0.65rem",
                fontFamily: 'Menlo, Monaco, Consolas, "Courier New", monospace',
              }}
            >
              Clear
            </button>
          </div>

          {/* Scrollable entries */}
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
            {filteredEntries.length === 0 ? (
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
                {entries.length === 0
                  ? "No commands executed yet..."
                  : "No matching entries"}
              </p>
            ) : (
              filteredEntries.map((entry) => {
                const lineCount = countOutputLines(entry.output);
                const shouldCollapse = lineCount > 5;
                const isExpanded = expandedIds.has(entry.id);

                return (
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
                      data-testid="terminal-command-row"
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
                          fontWeight: 700,
                          flex: 1,
                        }}
                      >
                        {entry.command}
                      </span>

                      {/* Copy button */}
                      <button
                        data-testid="terminal-copy-button"
                        onClick={() => copyCommand(entry.id, entry.command)}
                        title="Copy command"
                        style={{
                          background: "transparent",
                          border: "1px solid #30363d",
                          borderRadius: "4px",
                          color: copiedId === entry.id ? "#3fb950" : "#8b949e",
                          cursor: "pointer",
                          fontSize: "0.65rem",
                          padding: "0.1rem 0.3rem",
                          flexShrink: 0,
                          fontFamily: 'Menlo, Monaco, Consolas, "Courier New", monospace',
                          transition: "color 0.15s, border-color 0.15s",
                        }}
                      >
                        {copiedId === entry.id ? "\u2713" : "\u2398"}
                      </button>

                      {/* Timestamp */}
                      <span
                        data-testid="terminal-timestamp"
                        style={{
                          color: "#484f58",
                          fontSize: "0.6rem",
                          flexShrink: 0,
                        }}
                      >
                        {formatTime(entry.timestamp)}
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
                      <div style={{ marginTop: "0.3rem", marginLeft: "1.1rem" }}>
                        {shouldCollapse && !isExpanded ? (
                          <>
                            <pre
                              data-testid="terminal-output"
                              style={{
                                color: "#8b949e",
                                fontSize: "0.7rem",
                                margin: 0,
                                whiteSpace: "pre-wrap",
                                wordBreak: "break-word",
                                lineHeight: 1.4,
                                maxHeight: "105px",
                                overflow: "hidden",
                              }}
                            >
                              {entry.output.split("\n").slice(0, 5).join("\n")}
                            </pre>
                            <button
                              data-testid="terminal-expand-button"
                              onClick={() => toggleExpand(entry.id)}
                              style={{
                                background: "transparent",
                                border: "none",
                                color: "#58a6ff",
                                cursor: "pointer",
                                fontSize: "0.65rem",
                                padding: "0.2rem 0",
                                fontFamily: 'Menlo, Monaco, Consolas, "Courier New", monospace',
                              }}
                            >
                              Show {lineCount - 5} more lines...
                            </button>
                          </>
                        ) : (
                          <>
                            <pre
                              data-testid="terminal-output"
                              style={{
                                color: "#8b949e",
                                fontSize: "0.7rem",
                                margin: 0,
                                whiteSpace: "pre-wrap",
                                wordBreak: "break-word",
                                lineHeight: 1.4,
                                maxHeight: shouldCollapse ? "300px" : "150px",
                                overflow: "auto",
                              }}
                            >
                              {entry.output}
                            </pre>
                            {shouldCollapse && (
                              <button
                                data-testid="terminal-collapse-button"
                                onClick={() => toggleExpand(entry.id)}
                                style={{
                                  background: "transparent",
                                  border: "none",
                                  color: "#58a6ff",
                                  cursor: "pointer",
                                  fontSize: "0.65rem",
                                  padding: "0.2rem 0",
                                  fontFamily: 'Menlo, Monaco, Consolas, "Courier New", monospace',
                                }}
                              >
                                Show less
                              </button>
                            )}
                          </>
                        )}
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </>
      )}
    </div>
  );
}
