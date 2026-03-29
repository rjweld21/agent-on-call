"use client";

import { useState, useEffect, useRef } from "react";

export type ActivityType = "thinking" | "executing" | "tool_call" | "result";

export interface ActivityItem {
  id: string;
  type: ActivityType;
  text: string;
  timestamp: Date;
  detail?: string;
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
};

export function ThinkingPanel({ activities, isAgentWorking }: ThinkingPanelProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new activities arrive
  useEffect(() => {
    if (scrollRef.current && !isCollapsed) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [activities.length, isCollapsed]);

  return (
    <div
      data-testid="thinking-panel"
      style={{
        width: "100%",
        maxWidth: "500px",
        border: "1px solid #334155",
        borderRadius: "8px",
        background: "#1e293b",
        overflow: "hidden",
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
            maxHeight: "180px",
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
              const style = TYPE_STYLES[item.type];
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
                  <span
                    style={{
                      color: style.color,
                      fontWeight: 600,
                      marginRight: "0.4rem",
                      fontFamily:
                        item.type === "executing" ? "monospace" : "inherit",
                    }}
                  >
                    [{style.prefix}]
                  </span>
                  <span
                    style={{
                      color: "#cbd5e1",
                      fontStyle: style.fontStyle || "normal",
                      fontFamily:
                        item.type === "executing" ? "monospace" : "inherit",
                    }}
                  >
                    {item.text}
                  </span>
                  {item.detail && (
                    <div
                      style={{
                        color: "#64748b",
                        fontSize: "0.7rem",
                        marginTop: "0.15rem",
                        fontFamily: "monospace",
                        whiteSpace: "pre-wrap",
                        maxHeight: "60px",
                        overflow: "hidden",
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
