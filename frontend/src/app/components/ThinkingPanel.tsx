"use client";

import { useState, useEffect, useRef } from "react";

export type ActivityType = "thinking" | "executing" | "tool_call" | "result" | "system";

export interface ActivityItem {
  id: string;
  type: ActivityType;
  text: string;
  timestamp: Date;
  detail?: string;
  tool?: string;
  status?: "started" | "completed" | "failed";
}

interface ThinkingPanelProps {
  activities: ActivityItem[];
  isAgentWorking: boolean;
}

const TYPE_STYLES: Record<ActivityType, { color: string; prefix: string; fontStyle?: string }> = {
  thinking: { color: "#94a3b8", prefix: "Thinking", fontStyle: "italic" },
  executing: { color: "#22c55e", prefix: "Running", fontStyle: undefined },
  tool_call: { color: "#f59e0b", prefix: "Tool", fontStyle: undefined },
  result: { color: "#60a5fa", prefix: "Result", fontStyle: undefined },
  system: { color: "#38bdf8", prefix: "System", fontStyle: "italic" },
};

const STATUS_INDICATORS: Record<string, { symbol: string; color: string }> = {
  started: { symbol: "\u25CB", color: "#f59e0b" },    // ○ yellow circle
  completed: { symbol: "\u2713", color: "#22c55e" },   // ✓ green check
  failed: { symbol: "\u2717", color: "#ef4444" },      // ✗ red x
};

export function ThinkingPanel({ activities, isAgentWorking }: ThinkingPanelProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new activities arrive
  useEffect(() => {
    if (scrollRef.current && !isCollapsed) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [activities.length, isCollapsed]);

  const toggleExpanded = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  return (
    <div
      data-testid="thinking-panel"
      style={{
        width: "100%",
        border: "1px solid #334155",
        borderRadius: "0",
        background: "#1e293b",
        overflow: "hidden",
        display: "flex",
        flexDirection: "column" as const,
        flex: 1,
        minHeight: 0,
      }}
    >
      {/* Header */}
      <button
        data-testid="thinking-panel-toggle"
        onClick={() => setIsCollapsed(!isCollapsed)}
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          width: "100%",
          padding: "0.5rem 0.8rem",
          background: "none",
          border: "none",
          borderBottom: isCollapsed ? "none" : "1px solid #334155",
          color: "#e2e8f0",
          cursor: "pointer",
          fontSize: "0.85rem",
          fontWeight: 600,
          textAlign: "left",
        }}
      >
        <span>
          Agent Activity
          {isAgentWorking && (
            <span
              data-testid="thinking-indicator"
              style={{
                marginLeft: "0.5rem",
                color: "#f59e0b",
                fontSize: "0.75rem",
                fontWeight: 400,
              }}
            >
              (working...)
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
          data-testid="thinking-panel-content"
          style={{
            flex: 1,
            minHeight: 0,
            overflowY: "auto",
            padding: "0.5rem 0.8rem",
          }}
        >
          {activities.length === 0 ? (
            <p
              data-testid="thinking-empty"
              style={{
                color: "#475569",
                fontSize: "0.8rem",
                fontStyle: "italic",
                margin: 0,
              }}
            >
              No activity yet. The agent will show its thinking here...
            </p>
          ) : (
            activities.map((item) => {
              const typeStyle = TYPE_STYLES[item.type];
              const statusIndicator = item.status ? STATUS_INDICATORS[item.status] : null;
              const isExpanded = expandedIds.has(item.id);
              const hasDetail = !!item.detail;

              return (
                <div
                  key={item.id}
                  data-testid="activity-item"
                  style={{
                    padding: "0.25rem 0",
                    fontSize: "0.8rem",
                    borderBottom: "1px solid #1e293b",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "0.3rem",
                      cursor: hasDetail ? "pointer" : "default",
                    }}
                    onClick={hasDetail ? () => toggleExpanded(item.id) : undefined}
                    data-testid={hasDetail ? "activity-detail-toggle" : undefined}
                  >
                    {/* Status indicator */}
                    {statusIndicator && (
                      <span
                        data-testid="activity-status"
                        style={{
                          color: statusIndicator.color,
                          fontSize: "0.75rem",
                          flexShrink: 0,
                          width: "1rem",
                          textAlign: "center",
                        }}
                      >
                        {statusIndicator.symbol}
                      </span>
                    )}

                    {/* Type prefix */}
                    <span
                      style={{
                        color: typeStyle.color,
                        fontWeight: 600,
                        marginRight: "0.2rem",
                        fontFamily:
                          item.type === "executing" ? "monospace" : "inherit",
                        flexShrink: 0,
                      }}
                    >
                      [{typeStyle.prefix}]
                    </span>

                    {/* Summary text */}
                    <span
                      style={{
                        color: "#cbd5e1",
                        fontStyle: typeStyle.fontStyle || "normal",
                        fontFamily:
                          item.type === "executing" ? "monospace" : "inherit",
                        flex: 1,
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {item.text}
                    </span>

                    {/* Expand/collapse indicator */}
                    {hasDetail && (
                      <span
                        style={{
                          color: "#64748b",
                          fontSize: "0.65rem",
                          flexShrink: 0,
                          transform: isExpanded ? "rotate(0deg)" : "rotate(-90deg)",
                          transition: "transform 0.15s",
                        }}
                      >
                        &#9660;
                      </span>
                    )}
                  </div>

                  {/* Collapsible detail */}
                  {hasDetail && isExpanded && (
                    <div
                      data-testid="activity-detail"
                      style={{
                        color: "#64748b",
                        fontSize: "0.7rem",
                        marginTop: "0.15rem",
                        marginLeft: statusIndicator ? "1.3rem" : "0",
                        fontFamily: "monospace",
                        whiteSpace: "pre-wrap",
                        maxHeight: "120px",
                        overflow: "auto",
                        padding: "0.3rem",
                        background: "rgba(15, 23, 42, 0.5)",
                        borderRadius: "4px",
                        border: "1px solid #1e293b",
                      }}
                    >
                      {item.detail}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      )}
    </div>
  );
}
