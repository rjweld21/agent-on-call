import { describe, it, expect, beforeEach, vi } from "vitest";
import { SessionLogBuffer } from "./session-log";

describe("SessionLogBuffer", () => {
  let buffer: SessionLogBuffer;

  beforeEach(() => {
    buffer = new SessionLogBuffer();
  });

  it("starts with an empty log", () => {
    expect(buffer.entries()).toEqual([]);
  });

  it("adds entries with timestamp, level, component, and message", () => {
    buffer.info("connection", "Connected to room");
    const entries = buffer.entries();
    expect(entries).toHaveLength(1);
    expect(entries[0]).toMatchObject({
      level: "INFO",
      component: "connection",
      message: "Connected to room",
    });
    expect(entries[0].timestamp).toBeDefined();
  });

  it("supports debug, info, warn, error levels", () => {
    buffer.debug("test", "debug msg");
    buffer.info("test", "info msg");
    buffer.warn("test", "warn msg");
    buffer.error("test", "error msg");

    const levels = buffer.entries().map((e) => e.level);
    expect(levels).toEqual(["DEBUG", "INFO", "WARN", "ERROR"]);
  });

  it("formats entries as structured lines", () => {
    buffer.info("agent", "Greeting sent");
    const text = buffer.toText();
    // Should match: [TIMESTAMP] [INFO] [agent] Greeting sent
    expect(text).toMatch(
      /^\[\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}Z\] \[INFO\] \[agent\] Greeting sent$/
    );
  });

  it("clears the buffer", () => {
    buffer.info("test", "msg1");
    buffer.info("test", "msg2");
    buffer.clear();
    expect(buffer.entries()).toEqual([]);
  });

  it("saves to localStorage", () => {
    const mockSetItem = vi.fn();
    vi.stubGlobal("localStorage", { setItem: mockSetItem, getItem: vi.fn() });

    buffer.info("session", "test");
    buffer.saveToLocalStorage("test-session");

    expect(mockSetItem).toHaveBeenCalledWith(
      "aoc-session-log-test-session",
      expect.stringContaining("[INFO]")
    );

    vi.unstubAllGlobals();
  });

  it("generates a download blob", () => {
    buffer.info("session", "line1");
    buffer.error("agent", "line2");
    const blob = buffer.toBlob();
    expect(blob).toBeInstanceOf(Blob);
    expect(blob.type).toBe("text/plain");
  });

  it("limits buffer size to prevent memory leaks", () => {
    // Default max is 5000 entries
    for (let i = 0; i < 5100; i++) {
      buffer.info("test", `entry ${i}`);
    }
    expect(buffer.entries().length).toBeLessThanOrEqual(5000);
    // Should keep the newest entries
    const last = buffer.entries()[buffer.entries().length - 1];
    expect(last.message).toBe("entry 5099");
  });
});
