import { describe, it, expect } from "vitest";
import {
  formatElapsedTime,
  detectGap,
  getSessionStartTime,
  formatLocalTime,
  groupTranscriptEntries,
  GROUPING_WINDOW_MS,
} from "./transcript-time";

describe("formatElapsedTime", () => {
  it("formats zero milliseconds as 00:00:00", () => {
    expect(formatElapsedTime(0)).toBe("00:00:00");
  });

  it("formats negative values as 00:00:00", () => {
    expect(formatElapsedTime(-5000)).toBe("00:00:00");
  });

  it("formats seconds correctly", () => {
    expect(formatElapsedTime(45000)).toBe("00:00:45");
  });

  it("formats minutes and seconds", () => {
    expect(formatElapsedTime(125000)).toBe("00:02:05");
  });

  it("formats hours, minutes, and seconds", () => {
    expect(formatElapsedTime(3661000)).toBe("01:01:01");
  });
});

describe("detectGap", () => {
  it("returns null for gaps <= 60 seconds", () => {
    const a = new Date("2026-03-25T10:00:00");
    const b = new Date("2026-03-25T10:00:30");
    expect(detectGap(a, b)).toBeNull();
  });

  it("returns minute gap string for gaps > 60 seconds", () => {
    const a = new Date("2026-03-25T10:00:00");
    const b = new Date("2026-03-25T10:03:00");
    expect(detectGap(a, b)).toBe("3 min gap");
  });

  it("returns hour + minute gap for large gaps", () => {
    const a = new Date("2026-03-25T10:00:00");
    const b = new Date("2026-03-25T11:05:00");
    expect(detectGap(a, b)).toBe("1 hr 5 min gap");
  });
});

describe("getSessionStartTime", () => {
  it("returns null for empty array", () => {
    expect(getSessionStartTime([])).toBeNull();
  });

  it("returns first entry timestamp", () => {
    const date = new Date("2026-03-25T10:00:00");
    expect(getSessionStartTime([{ timestamp: date }])).toBe(date);
  });
});

describe("formatLocalTime", () => {
  it("returns a string containing the hour and minute", () => {
    const date = new Date("2026-03-25T14:35:00");
    const result = formatLocalTime(date);
    // Should contain "2:35" (12h) or "14:35" (24h) depending on locale
    expect(result).toMatch(/\d{1,2}:\d{2}/);
  });

  it("handles midnight", () => {
    const date = new Date("2026-03-25T00:00:00");
    const result = formatLocalTime(date);
    expect(result).toMatch(/\d{1,2}:\d{2}/);
  });

  it("handles noon", () => {
    const date = new Date("2026-03-25T12:00:00");
    const result = formatLocalTime(date);
    expect(result).toMatch(/\d{1,2}:\d{2}/);
  });

  it("returns different strings for different times", () => {
    const morning = formatLocalTime(new Date("2026-03-25T09:15:00"));
    const evening = formatLocalTime(new Date("2026-03-25T21:45:00"));
    expect(morning).not.toBe(evening);
  });
});

describe("GROUPING_WINDOW_MS", () => {
  it("is exported and equals 2000", () => {
    expect(GROUPING_WINDOW_MS).toBe(2000);
  });
});

describe("groupTranscriptEntries", () => {
  const makeEntry = (
    id: string,
    speaker: "user" | "agent" | "user-text" | "system",
    text: string,
    timeMs: number,
  ) => ({
    id,
    speaker,
    text,
    timestamp: new Date(timeMs),
  });

  it("returns empty array for empty input", () => {
    expect(groupTranscriptEntries([])).toEqual([]);
  });

  it("returns one group for a single entry", () => {
    const entries = [makeEntry("a", "user", "hello", 1000)];
    const groups = groupTranscriptEntries(entries);
    expect(groups).toHaveLength(1);
    expect(groups[0].ids).toEqual(["a"]);
    expect(groups[0].text).toBe("hello");
    expect(groups[0].speaker).toBe("user");
  });

  it("merges consecutive same-speaker entries within the grouping window", () => {
    const entries = [
      makeEntry("a", "user", "I was thinking", 1000),
      makeEntry("b", "user", "about the database", 2500), // 1.5s gap < 2s
    ];
    const groups = groupTranscriptEntries(entries);
    expect(groups).toHaveLength(1);
    expect(groups[0].ids).toEqual(["a", "b"]);
    expect(groups[0].text).toBe("I was thinking about the database");
    expect(groups[0].timestamp.getTime()).toBe(1000);
    expect(groups[0].lastTimestamp.getTime()).toBe(2500);
  });

  it("does not merge same-speaker entries beyond the grouping window", () => {
    const entries = [
      makeEntry("a", "user", "first", 1000),
      makeEntry("b", "user", "second", 4000), // 3s gap > 2s
    ];
    const groups = groupTranscriptEntries(entries);
    expect(groups).toHaveLength(2);
    expect(groups[0].text).toBe("first");
    expect(groups[1].text).toBe("second");
  });

  it("never merges entries from different speakers", () => {
    const entries = [
      makeEntry("a", "user", "hello", 1000),
      makeEntry("b", "agent", "hi there", 1500), // 0.5s gap, different speaker
    ];
    const groups = groupTranscriptEntries(entries);
    expect(groups).toHaveLength(2);
    expect(groups[0].speaker).toBe("user");
    expect(groups[1].speaker).toBe("agent");
  });

  it("merges three rapid entries from the same speaker", () => {
    const entries = [
      makeEntry("a", "agent", "Let me", 1000),
      makeEntry("b", "agent", "think about", 2000),   // 1s gap
      makeEntry("c", "agent", "that for a moment", 3500), // 1.5s gap
    ];
    const groups = groupTranscriptEntries(entries);
    expect(groups).toHaveLength(1);
    expect(groups[0].text).toBe("Let me think about that for a moment");
    expect(groups[0].ids).toEqual(["a", "b", "c"]);
  });

  it("preserves first timestamp for display and last timestamp for gap detection", () => {
    const entries = [
      makeEntry("a", "user", "one", 1000),
      makeEntry("b", "user", "two", 2000),
    ];
    const groups = groupTranscriptEntries(entries);
    expect(groups[0].timestamp.getTime()).toBe(1000);
    expect(groups[0].lastTimestamp.getTime()).toBe(2000);
  });

  it("accepts a custom grouping window", () => {
    const entries = [
      makeEntry("a", "user", "first", 1000),
      makeEntry("b", "user", "second", 4000), // 3s gap
    ];
    // With 5s window, should merge
    const groups = groupTranscriptEntries(entries, 5000);
    expect(groups).toHaveLength(1);
    expect(groups[0].text).toBe("first second");
  });

  it("handles mixed speakers with interleaved grouping", () => {
    const entries = [
      makeEntry("a", "user", "hey", 1000),
      makeEntry("b", "user", "there", 2000),     // merge with a
      makeEntry("c", "agent", "hello", 2500),     // new group
      makeEntry("d", "agent", "friend", 3000),    // merge with c
      makeEntry("e", "user", "how are you", 3500), // new group
    ];
    const groups = groupTranscriptEntries(entries);
    expect(groups).toHaveLength(3);
    expect(groups[0].text).toBe("hey there");
    expect(groups[1].text).toBe("hello friend");
    expect(groups[2].text).toBe("how are you");
  });

  it("never merges system messages with adjacent entries", () => {
    const entries = [
      makeEntry("a", "system", "[Agent joined the call]", 1000),
      makeEntry("b", "system", "[Agent left the call]", 1500), // within window, same speaker
    ];
    const groups = groupTranscriptEntries(entries);
    expect(groups).toHaveLength(2);
    expect(groups[0].text).toBe("[Agent joined the call]");
    expect(groups[1].text).toBe("[Agent left the call]");
  });

  it("keeps system messages separate from surrounding entries", () => {
    const entries = [
      makeEntry("a", "user", "hello", 1000),
      makeEntry("b", "system", "[Agent joined the call]", 1500),
      makeEntry("c", "agent", "Hi there!", 2000),
    ];
    const groups = groupTranscriptEntries(entries);
    expect(groups).toHaveLength(3);
    expect(groups[0].speaker).toBe("user");
    expect(groups[1].speaker).toBe("system");
    expect(groups[2].speaker).toBe("agent");
  });

  it("system message has correct speaker type", () => {
    const entries = [
      makeEntry("a", "system", "[Agent joined the call]", 1000),
    ];
    const groups = groupTranscriptEntries(entries);
    expect(groups).toHaveLength(1);
    expect(groups[0].speaker).toBe("system");
    expect(groups[0].text).toBe("[Agent joined the call]");
  });
});
