import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ThinkingPanel, type ActivityItem } from "./ThinkingPanel";

const mockActivities: ActivityItem[] = [
  {
    id: "1",
    type: "thinking",
    text: "Analyzing the request...",
    timestamp: new Date("2026-03-25T10:00:00"),
  },
  {
    id: "2",
    type: "executing",
    text: "git status",
    timestamp: new Date("2026-03-25T10:00:01"),
    detail: "On branch main\nnothing to commit",
  },
  {
    id: "3",
    type: "tool_call",
    text: "read_file /workspace/README.md",
    timestamp: new Date("2026-03-25T10:00:02"),
  },
  {
    id: "4",
    type: "result",
    text: "Found 3 test files",
    timestamp: new Date("2026-03-25T10:00:03"),
  },
];

describe("ThinkingPanel", () => {
  it("renders the panel with header", () => {
    render(<ThinkingPanel activities={[]} isAgentWorking={false} />);
    expect(screen.getByTestId("thinking-panel")).toBeInTheDocument();
    expect(screen.getByText("Agent Activity")).toBeInTheDocument();
  });

  it("shows empty state when no activities", () => {
    render(<ThinkingPanel activities={[]} isAgentWorking={false} />);
    expect(screen.getByTestId("thinking-empty")).toBeInTheDocument();
    expect(screen.getByText(/No activity yet/)).toBeInTheDocument();
  });

  it("renders activity items", () => {
    render(<ThinkingPanel activities={mockActivities} isAgentWorking={false} />);
    const items = screen.getAllByTestId("activity-item");
    expect(items).toHaveLength(4);
  });

  it("shows correct type prefixes", () => {
    render(<ThinkingPanel activities={mockActivities} isAgentWorking={false} />);
    expect(screen.getByText("[Thinking]")).toBeInTheDocument();
    expect(screen.getByText("[Running]")).toBeInTheDocument();
    expect(screen.getByText("[Tool]")).toBeInTheDocument();
    expect(screen.getByText("[Result]")).toBeInTheDocument();
  });

  it("shows activity text", () => {
    render(<ThinkingPanel activities={mockActivities} isAgentWorking={false} />);
    expect(screen.getByText("Analyzing the request...")).toBeInTheDocument();
    expect(screen.getByText("git status")).toBeInTheDocument();
  });

  it("shows detail when present", () => {
    render(<ThinkingPanel activities={mockActivities} isAgentWorking={false} />);
    expect(screen.getByText(/On branch main/)).toBeInTheDocument();
  });

  it("shows working indicator when agent is working", () => {
    render(<ThinkingPanel activities={[]} isAgentWorking={true} />);
    expect(screen.getByTestId("thinking-indicator")).toBeInTheDocument();
    expect(screen.getByText("(working...)")).toBeInTheDocument();
  });

  it("does not show working indicator when agent is idle", () => {
    render(<ThinkingPanel activities={[]} isAgentWorking={false} />);
    expect(screen.queryByTestId("thinking-indicator")).not.toBeInTheDocument();
  });

  it("can be collapsed and expanded", () => {
    render(<ThinkingPanel activities={mockActivities} isAgentWorking={false} />);

    // Initially expanded
    expect(screen.getByTestId("thinking-panel-content")).toBeInTheDocument();

    // Click to collapse
    fireEvent.click(screen.getByTestId("thinking-panel-toggle"));
    expect(screen.queryByTestId("thinking-panel-content")).not.toBeInTheDocument();

    // Click to expand
    fireEvent.click(screen.getByTestId("thinking-panel-toggle"));
    expect(screen.getByTestId("thinking-panel-content")).toBeInTheDocument();
  });

  it("renders different activity types with visual distinction", () => {
    render(
      <ThinkingPanel
        activities={[
          { id: "t", type: "thinking", text: "thinking text", timestamp: new Date() },
          { id: "e", type: "executing", text: "exec text", timestamp: new Date() },
        ]}
        isAgentWorking={false}
      />
    );
    // Both items rendered
    expect(screen.getByText("thinking text")).toBeInTheDocument();
    expect(screen.getByText("exec text")).toBeInTheDocument();
  });
});
