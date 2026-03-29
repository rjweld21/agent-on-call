import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { TerminalPanel, type TerminalEntry } from "./TerminalPanel";

const mockEntries: TerminalEntry[] = [
  {
    id: "1",
    timestamp: new Date("2026-03-25T10:00:00"),
    command: "ls -la",
    output: "total 42\ndrwxr-xr-x  5 user group  160 Mar 25 10:00 .\n",
    exitCode: 0,
    status: "completed",
    tool: "exec_command",
  },
  {
    id: "2",
    timestamp: new Date("2026-03-25T10:00:05"),
    command: "git status",
    output: "On branch main\nnothing to commit, working tree clean",
    exitCode: 0,
    status: "completed",
    tool: "git_status",
  },
  {
    id: "3",
    timestamp: new Date("2026-03-25T10:00:10"),
    command: "npm test",
    output: "Error: test failed",
    exitCode: 1,
    status: "failed",
    tool: "exec_command",
  },
];

describe("TerminalPanel", () => {
  it("renders the panel with header", () => {
    render(<TerminalPanel entries={[]} />);
    expect(screen.getByTestId("terminal-panel")).toBeInTheDocument();
    expect(screen.getByText("Terminal Output")).toBeInTheDocument();
  });

  it("shows empty state when no entries", () => {
    render(<TerminalPanel entries={[]} />);
    expect(screen.getByTestId("terminal-empty")).toBeInTheDocument();
    expect(
      screen.getByText(/No commands executed yet/)
    ).toBeInTheDocument();
  });

  it("renders terminal entries", () => {
    render(<TerminalPanel entries={mockEntries} />);
    const items = screen.getAllByTestId("terminal-entry");
    expect(items).toHaveLength(3);
  });

  it("shows command text with $ prompt", () => {
    render(<TerminalPanel entries={mockEntries} />);
    const prompts = screen.getAllByTestId("terminal-prompt");
    expect(prompts).toHaveLength(3);
    expect(prompts[0]).toHaveTextContent("$");

    const commands = screen.getAllByTestId("terminal-command");
    expect(commands[0]).toHaveTextContent("ls -la");
    expect(commands[1]).toHaveTextContent("git status");
    expect(commands[2]).toHaveTextContent("npm test");
  });

  it("shows command text in bold (fontWeight 700)", () => {
    render(<TerminalPanel entries={mockEntries} />);
    const commands = screen.getAllByTestId("terminal-command");
    expect(commands[0].style.fontWeight).toBe("700");
  });

  it("shows command output", () => {
    render(<TerminalPanel entries={mockEntries} />);
    const outputs = screen.getAllByTestId("terminal-output");
    expect(outputs.length).toBeGreaterThan(0);
    expect(outputs[0]).toHaveTextContent("total 42");
  });

  it("shows green exit code for success (0)", () => {
    render(<TerminalPanel entries={[mockEntries[0]]} />);
    const exitCode = screen.getByTestId("terminal-exit-code");
    expect(exitCode).toHaveTextContent("0");
    expect(exitCode.style.color).toBe("rgb(63, 185, 80)"); // #3fb950
  });

  it("shows red exit code for failure (non-zero)", () => {
    render(<TerminalPanel entries={[mockEntries[2]]} />);
    const exitCode = screen.getByTestId("terminal-exit-code");
    expect(exitCode).toHaveTextContent("1");
    expect(exitCode.style.color).toBe("rgb(248, 81, 73)"); // #f85149
  });

  it("shows running indicator for in-progress commands", () => {
    const runningEntry: TerminalEntry = {
      id: "r1",
      timestamp: new Date(),
      command: "pytest tests/",
      output: "",
      exitCode: 0,
      status: "running",
    };
    render(<TerminalPanel entries={[runningEntry]} />);
    expect(screen.getByTestId("terminal-running-badge")).toBeInTheDocument();
    expect(screen.getByTestId("terminal-running-indicator")).toBeInTheDocument();
    // Should NOT show exit code when running
    expect(screen.queryByTestId("terminal-exit-code")).not.toBeInTheDocument();
    // Should NOT show output when running
    expect(screen.queryByTestId("terminal-output")).not.toBeInTheDocument();
  });

  it("collapses and expands on toggle click", () => {
    render(<TerminalPanel entries={mockEntries} />);
    expect(screen.getByTestId("terminal-panel-content")).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("terminal-panel-toggle"));
    expect(
      screen.queryByTestId("terminal-panel-content")
    ).not.toBeInTheDocument();

    fireEvent.click(screen.getByTestId("terminal-panel-toggle"));
    expect(screen.getByTestId("terminal-panel-content")).toBeInTheDocument();
  });

  it("shows entry count in header", () => {
    render(<TerminalPanel entries={mockEntries} />);
    // 3 completed/failed out of 3 total
    expect(screen.getByTestId("terminal-entry-count")).toHaveTextContent(
      "(3/3)"
    );
  });

  it("does not show entry count when empty", () => {
    render(<TerminalPanel entries={[]} />);
    expect(
      screen.queryByTestId("terminal-entry-count")
    ).not.toBeInTheDocument();
  });

  it("has monospace font family", () => {
    render(<TerminalPanel entries={[]} />);
    const panel = screen.getByTestId("terminal-panel");
    expect(panel.style.fontFamily).toContain("Menlo");
    expect(panel.style.fontFamily).toContain("monospace");
  });

  it("has dark terminal background", () => {
    render(<TerminalPanel entries={[]} />);
    const panel = screen.getByTestId("terminal-panel");
    expect(panel.style.background).toBe("rgb(13, 17, 23)"); // #0d1117
  });

  // === New tests for #66 enhancements ===

  describe("copy button", () => {
    beforeEach(() => {
      Object.assign(navigator, {
        clipboard: {
          writeText: vi.fn().mockResolvedValue(undefined),
        },
      });
    });

    it("renders a copy button for each entry", () => {
      render(<TerminalPanel entries={mockEntries} />);
      const copyButtons = screen.getAllByTestId("terminal-copy-button");
      expect(copyButtons).toHaveLength(3);
    });

    it("copies command to clipboard on click", async () => {
      render(<TerminalPanel entries={[mockEntries[0]]} />);
      const copyBtn = screen.getByTestId("terminal-copy-button");
      fireEvent.click(copyBtn);
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith("ls -la");
    });
  });

  describe("timestamp", () => {
    it("shows HH:MM:SS timestamp for each entry", () => {
      render(<TerminalPanel entries={[mockEntries[0]]} />);
      const timestamp = screen.getByTestId("terminal-timestamp");
      // 10:00:00 in local time
      expect(timestamp).toBeInTheDocument();
      expect(timestamp.textContent).toMatch(/\d{2}:\d{2}:\d{2}/);
    });
  });

  describe("collapsible output", () => {
    it("collapses output with > 5 lines by default", () => {
      const longOutput = Array.from({ length: 10 }, (_, i) => `line ${i + 1}`).join("\n");
      const entry: TerminalEntry = {
        id: "long1",
        timestamp: new Date("2026-03-25T10:00:00"),
        command: "cat file.txt",
        output: longOutput,
        exitCode: 0,
        status: "completed",
      };
      render(<TerminalPanel entries={[entry]} />);
      const expandBtn = screen.getByTestId("terminal-expand-button");
      expect(expandBtn).toBeInTheDocument();
      expect(expandBtn).toHaveTextContent(/5 more lines/);
    });

    it("expands output on click", () => {
      const longOutput = Array.from({ length: 10 }, (_, i) => `line ${i + 1}`).join("\n");
      const entry: TerminalEntry = {
        id: "long2",
        timestamp: new Date("2026-03-25T10:00:00"),
        command: "cat file.txt",
        output: longOutput,
        exitCode: 0,
        status: "completed",
      };
      render(<TerminalPanel entries={[entry]} />);
      fireEvent.click(screen.getByTestId("terminal-expand-button"));
      // After expanding, should show collapse button
      expect(screen.getByTestId("terminal-collapse-button")).toBeInTheDocument();
      // Full output should now be visible
      const output = screen.getByTestId("terminal-output");
      expect(output.textContent).toContain("line 10");
    });

    it("does not show expand button for short output (<= 5 lines)", () => {
      render(<TerminalPanel entries={[mockEntries[0]]} />);
      expect(screen.queryByTestId("terminal-expand-button")).not.toBeInTheDocument();
    });
  });

  describe("filter bar", () => {
    it("renders filter bar with All, Commands, Errors buttons", () => {
      render(<TerminalPanel entries={mockEntries} />);
      expect(screen.getByTestId("terminal-filter-bar")).toBeInTheDocument();
      expect(screen.getByTestId("terminal-filter-all")).toBeInTheDocument();
      expect(screen.getByTestId("terminal-filter-commands")).toBeInTheDocument();
      expect(screen.getByTestId("terminal-filter-errors")).toBeInTheDocument();
    });

    it("filters to errors only when errors button clicked", () => {
      render(<TerminalPanel entries={mockEntries} />);
      fireEvent.click(screen.getByTestId("terminal-filter-errors"));
      const items = screen.getAllByTestId("terminal-entry");
      expect(items).toHaveLength(1);
      const commands = screen.getAllByTestId("terminal-command");
      expect(commands[0]).toHaveTextContent("npm test");
    });

    it("shows all entries when All is clicked after filtering", () => {
      render(<TerminalPanel entries={mockEntries} />);
      fireEvent.click(screen.getByTestId("terminal-filter-errors"));
      expect(screen.getAllByTestId("terminal-entry")).toHaveLength(1);
      fireEvent.click(screen.getByTestId("terminal-filter-all"));
      expect(screen.getAllByTestId("terminal-entry")).toHaveLength(3);
    });

    it("shows error count in errors filter button", () => {
      render(<TerminalPanel entries={mockEntries} />);
      const errorsBtn = screen.getByTestId("terminal-filter-errors");
      expect(errorsBtn).toHaveTextContent("Errors (1)");
    });
  });

  describe("clear button", () => {
    it("renders a clear button", () => {
      render(<TerminalPanel entries={mockEntries} />);
      expect(screen.getByTestId("terminal-clear-button")).toBeInTheDocument();
    });

    it("calls onClear callback when clear is clicked", () => {
      const onClear = vi.fn();
      render(<TerminalPanel entries={mockEntries} onClear={onClear} />);
      fireEvent.click(screen.getByTestId("terminal-clear-button"));
      expect(onClear).toHaveBeenCalledOnce();
    });
  });

  describe("no matching entries message", () => {
    it("shows 'No matching entries' when filter results in empty list", () => {
      const successOnly: TerminalEntry[] = [mockEntries[0]]; // only success
      render(<TerminalPanel entries={successOnly} />);
      fireEvent.click(screen.getByTestId("terminal-filter-errors"));
      expect(screen.getByTestId("terminal-empty")).toHaveTextContent("No matching entries");
    });
  });
});
