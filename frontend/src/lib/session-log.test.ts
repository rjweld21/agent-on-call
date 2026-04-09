import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
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

  describe("startAutoSave / stopAutoSave", () => {
    beforeEach(() => {
      vi.useFakeTimers();
      vi.stubGlobal("localStorage", { setItem: vi.fn(), getItem: vi.fn() });
    });

    afterEach(() => {
      vi.useRealTimers();
      vi.unstubAllGlobals();
    });

    it("periodically calls saveToLocalStorage", () => {
      const spy = vi.spyOn(buffer, "saveToLocalStorage");
      buffer.startAutoSave(1000, "sess-1");

      // Should not fire immediately
      expect(spy).not.toHaveBeenCalled();

      vi.advanceTimersByTime(1000);
      expect(spy).toHaveBeenCalledTimes(1);
      expect(spy).toHaveBeenCalledWith("sess-1");

      vi.advanceTimersByTime(2000);
      expect(spy).toHaveBeenCalledTimes(3);

      buffer.stopAutoSave();
    });

    it("stopAutoSave clears the interval", () => {
      const spy = vi.spyOn(buffer, "saveToLocalStorage");
      buffer.startAutoSave(1000, "sess-1");

      vi.advanceTimersByTime(1000);
      expect(spy).toHaveBeenCalledTimes(1);

      buffer.stopAutoSave();
      vi.advanceTimersByTime(5000);
      expect(spy).toHaveBeenCalledTimes(1); // No more calls
    });

    it("calling startAutoSave twice replaces the previous interval", () => {
      const spy = vi.spyOn(buffer, "saveToLocalStorage");
      buffer.startAutoSave(1000, "sess-1");
      buffer.startAutoSave(2000, "sess-2");

      vi.advanceTimersByTime(2000);
      // Should only have fired once (at 2s for the second interval)
      expect(spy).toHaveBeenCalledTimes(1);
      expect(spy).toHaveBeenCalledWith("sess-2");

      buffer.stopAutoSave();
    });

    it("stopAutoSave is safe to call when no interval is running", () => {
      expect(() => buffer.stopAutoSave()).not.toThrow();
    });
  });

  describe("setupBeforeUnload / teardownBeforeUnload", () => {
    let addSpy: ReturnType<typeof vi.spyOn>;
    let removeSpy: ReturnType<typeof vi.spyOn>;

    beforeEach(() => {
      addSpy = vi.spyOn(window, "addEventListener");
      removeSpy = vi.spyOn(window, "removeEventListener");
      vi.stubGlobal("localStorage", { setItem: vi.fn(), getItem: vi.fn() });
    });

    afterEach(() => {
      vi.unstubAllGlobals();
      addSpy.mockRestore();
      removeSpy.mockRestore();
    });

    it("registers a beforeunload listener that saves to storage", () => {
      buffer.info("test", "some data");
      buffer.setupBeforeUnload("sess-1");

      expect(addSpy).toHaveBeenCalledWith("beforeunload", expect.any(Function));

      // Simulate the beforeunload event
      const handler = addSpy.mock.calls.find(
        (c: unknown[]) => c[0] === "beforeunload"
      )?.[1] as EventListener;
      expect(handler).toBeDefined();

      const saveSpy = vi.spyOn(buffer, "saveToLocalStorage");
      handler(new Event("beforeunload"));
      expect(saveSpy).toHaveBeenCalledWith("sess-1");
    });

    it("teardownBeforeUnload removes the listener", () => {
      buffer.setupBeforeUnload("sess-1");
      buffer.teardownBeforeUnload();

      expect(removeSpy).toHaveBeenCalledWith(
        "beforeunload",
        expect.any(Function)
      );
    });

    it("teardownBeforeUnload is safe to call without setup", () => {
      expect(() => buffer.teardownBeforeUnload()).not.toThrow();
    });

    it("calling setupBeforeUnload twice replaces the listener", () => {
      buffer.setupBeforeUnload("sess-1");
      buffer.setupBeforeUnload("sess-2");

      // Should have removed the first listener before adding the second
      expect(removeSpy).toHaveBeenCalledTimes(1);
      expect(addSpy).toHaveBeenCalledTimes(2);

      buffer.teardownBeforeUnload();
    });
  });
});
