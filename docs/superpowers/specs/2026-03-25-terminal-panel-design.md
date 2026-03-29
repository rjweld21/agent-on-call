# Terminal Output Panel Design

## Problem

When the agent executes shell commands, git operations, or file edits, users see action summaries in the ThinkingPanel (e.g., "[Running] ls -la"), but there is no dedicated terminal-style view showing full command output. Users need a distinct panel with monospace rendering to see what the agent is doing technically.

## Design

### TerminalPanel Component

New component at `frontend/src/app/components/TerminalPanel.tsx`.

**Data model:**
```typescript
interface TerminalEntry {
  id: string;
  timestamp: Date;
  command: string;
  output: string;
  exitCode: number;
  status: "running" | "completed" | "failed";
}
```

**Props:**
```typescript
interface TerminalPanelProps {
  entries: TerminalEntry[];
}
```

### Visual Design

- Dark terminal background: `#0d1117` (darker than the existing `#1e293b` panels)
- Monospace font: system monospace (`"Menlo, Monaco, Consolas, 'Courier New', monospace"`)
- Command prefix: green `$` prompt, white command text
- Output: dim gray (`#8b949e`)
- Exit code badge: green `0`, red for non-zero
- Collapsible (like ThinkingPanel) with header "Terminal Output"
- Max height 300px, scrollable, auto-scroll to bottom
- Empty state: "No commands executed yet..."

### Data Flow

The TerminalPanel receives its entries from the existing `agent_action` data channel messages. The `page.tsx` component already parses `agent_action` events and stores them as `ActivityItem[]`. We will:

1. Filter `agent_action` events where `tool === "exec_command"` (and similar command tools)
2. Build `TerminalEntry` objects from the action events:
   - `status === "started"` -> create entry with `status: "running"`
   - `status === "completed"` or `status === "failed"` -> update entry with output and exit code
3. Pass filtered entries to `TerminalPanel`

This approach reuses the existing data channel infrastructure -- no new backend changes needed.

### Exit Code Parsing

The `exec_command` result detail contains output like `"Exit code: 0\n\nStdout:\n..."`. We parse this to extract the exit code and output text.

### Layout Integration

Add TerminalPanel to `page.tsx` between ThinkingPanel and the Transcript section. This creates a three-panel layout:
1. ThinkingPanel (agent activity summary)
2. TerminalPanel (command output detail)
3. Transcript (conversation)

## Testing Strategy

### Unit Tests (`TerminalPanel.test.tsx`)
- Renders empty state
- Renders command entries
- Shows exit code with correct color (green/red)
- Auto-scrolls on new entries
- Collapse/expand toggle works
- Running commands show spinner/indicator

### Playwright E2E
- Panel visible on room page
- Panel collapsible
- Commands appear when agent executes them (mock or real)
