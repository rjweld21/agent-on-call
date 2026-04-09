/**
 * In-memory session debug log buffer for the frontend.
 *
 * Collects structured log entries during a call and provides
 * methods to save to localStorage or download as a file.
 */

export interface LogEntry {
  timestamp: string;
  level: string;
  component: string;
  message: string;
}

const DEFAULT_MAX_ENTRIES = 5000;

export class SessionLogBuffer {
  private _entries: LogEntry[] = [];
  private _maxEntries: number;

  constructor(maxEntries: number = DEFAULT_MAX_ENTRIES) {
    this._maxEntries = maxEntries;
  }

  /** Get all log entries. */
  entries(): LogEntry[] {
    return [...this._entries];
  }

  /** Add a log entry. */
  private _add(level: string, component: string, message: string): void {
    this._entries.push({
      timestamp: new Date().toISOString(),
      level,
      component,
      message,
    });
    // Trim oldest entries if over limit
    if (this._entries.length > this._maxEntries) {
      this._entries = this._entries.slice(this._entries.length - this._maxEntries);
    }
  }

  debug(component: string, message: string): void {
    this._add("DEBUG", component, message);
  }

  info(component: string, message: string): void {
    this._add("INFO", component, message);
  }

  warn(component: string, message: string): void {
    this._add("WARN", component, message);
  }

  error(component: string, message: string): void {
    this._add("ERROR", component, message);
  }

  /** Clear all entries. */
  clear(): void {
    this._entries = [];
  }

  /** Format all entries as structured text lines. */
  toText(): string {
    return this._entries
      .map((e) => `[${e.timestamp}] [${e.level}] [${e.component}] ${e.message}`)
      .join("\n");
  }

  /** Save log text to localStorage. */
  saveToLocalStorage(sessionId: string): void {
    try {
      localStorage.setItem(`aoc-session-log-${sessionId}`, this.toText());
    } catch {
      // localStorage may be full or unavailable
    }
  }

  /** Create a Blob suitable for file download. */
  toBlob(): Blob {
    return new Blob([this.toText()], { type: "text/plain" });
  }
}
