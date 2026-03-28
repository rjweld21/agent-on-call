import { describe, it, expect } from "vitest";
import {
  formatElapsedTime,
  detectGap,
  getSessionStartTime,
} from "./transcript-time";

describe("formatElapsedTime", () => {
  it("returns 00:00:00 for 0 milliseconds", () => {
    expect(formatElapsedTime(0)).toBe("00:00:00");
  });

  it("returns 00:00:01 for 1000 milliseconds", () => {
    expect(formatElapsedTime(1000)).toBe("00:00:01");
  });

  it("returns 00:01:01 for 61000 milliseconds", () => {
    expect(formatElapsedTime(61000)).toBe("00:01:01");
  });

  it("returns 01:01:01 for 3661000 milliseconds", () => {
    expect(formatElapsedTime(3661000)).toBe("01:01:01");
  });

  it("returns 00:00:00 for negative input", () => {
    expect(formatElapsedTime(-5000)).toBe("00:00:00");
  });

  it("handles hours greater than 99", () => {
    // 100 hours = 360000000 ms
    expect(formatElapsedTime(360000000)).toBe("100:00:00");
  });

  it("returns 00:00:30 for 30000 milliseconds", () => {
    expect(formatElapsedTime(30000)).toBe("00:00:30");
  });

  it("returns 00:05:00 for 300000 milliseconds", () => {
    expect(formatElapsedTime(300000)).toBe("00:05:00");
  });
});

describe("detectGap", () => {
  it("returns null for a gap of 30 seconds", () => {
    const prev = new Date("2026-01-01T00:00:00Z");
    const curr = new Date("2026-01-01T00:00:30Z");
    expect(detectGap(prev, curr)).toBeNull();
  });

  it("returns null for exactly 60 seconds", () => {
    const prev = new Date("2026-01-01T00:00:00Z");
    const curr = new Date("2026-01-01T00:01:00Z");
    expect(detectGap(prev, curr)).toBeNull();
  });

  it('returns "1 min gap" for 61 seconds', () => {
    const prev = new Date("2026-01-01T00:00:00Z");
    const curr = new Date("2026-01-01T00:01:01Z");
    expect(detectGap(prev, curr)).toBe("1 min gap");
  });

  it('returns "2 min gap" for 120 seconds', () => {
    const prev = new Date("2026-01-01T00:00:00Z");
    const curr = new Date("2026-01-01T00:02:00Z");
    expect(detectGap(prev, curr)).toBe("2 min gap");
  });

  it('returns "2 min gap" for 150 seconds', () => {
    const prev = new Date("2026-01-01T00:00:00Z");
    const curr = new Date("2026-01-01T00:02:30Z");
    expect(detectGap(prev, curr)).toBe("2 min gap");
  });

  it('returns "1 hr 0 min gap" for 3600 seconds', () => {
    const prev = new Date("2026-01-01T00:00:00Z");
    const curr = new Date("2026-01-01T01:00:00Z");
    expect(detectGap(prev, curr)).toBe("1 hr 0 min gap");
  });

  it('returns "1 hr 5 min gap" for 3900 seconds', () => {
    const prev = new Date("2026-01-01T00:00:00Z");
    const curr = new Date("2026-01-01T01:05:00Z");
    expect(detectGap(prev, curr)).toBe("1 hr 5 min gap");
  });

  it('returns "2 hr 30 min gap" for 9000 seconds', () => {
    const prev = new Date("2026-01-01T00:00:00Z");
    const curr = new Date("2026-01-01T02:30:00Z");
    expect(detectGap(prev, curr)).toBe("2 hr 30 min gap");
  });
});

describe("getSessionStartTime", () => {
  it("returns null for an empty array", () => {
    expect(getSessionStartTime([])).toBeNull();
  });

  it("returns the timestamp of a single entry", () => {
    const date = new Date("2026-01-01T12:00:00Z");
    expect(getSessionStartTime([{ timestamp: date }])).toBe(date);
  });

  it("returns the timestamp of the first entry", () => {
    const first = new Date("2026-01-01T12:00:00Z");
    const second = new Date("2026-01-01T12:05:00Z");
    expect(
      getSessionStartTime([{ timestamp: first }, { timestamp: second }]),
    ).toBe(first);
  });
});
