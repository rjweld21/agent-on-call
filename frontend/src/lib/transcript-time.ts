/**
 * Format elapsed milliseconds as HH:MM:SS.
 * Negative values are clamped to 00:00:00.
 */
export function formatElapsedTime(elapsedMs: number): string {
  if (elapsedMs < 0) elapsedMs = 0;

  const totalSeconds = Math.floor(elapsedMs / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  const pad = (n: number, width: number = 2) =>
    n.toString().padStart(width, "0");

  // Hours may exceed 99, so use at least 2 digits
  const hh = hours >= 100 ? hours.toString() : pad(hours);
  return `${hh}:${pad(minutes)}:${pad(seconds)}`;
}

/**
 * Detect a pause gap between two timestamps.
 * Returns a human-readable string if gap > 60 seconds, null otherwise.
 */
export function detectGap(
  prevTimestamp: Date,
  currTimestamp: Date,
): string | null {
  const gapMs = currTimestamp.getTime() - prevTimestamp.getTime();
  const gapSeconds = Math.floor(gapMs / 1000);

  if (gapSeconds <= 60) return null;

  const hours = Math.floor(gapSeconds / 3600);
  const minutes = Math.floor((gapSeconds % 3600) / 60);

  if (hours >= 1) {
    return `${hours} hr ${minutes} min gap`;
  }

  return `${minutes} min gap`;
}

/**
 * Get the session start time from transcript entries.
 * Returns the timestamp of the first entry, or null if empty.
 */
export function getSessionStartTime(
  entries: { timestamp: Date }[],
): Date | null {
  if (entries.length === 0) return null;
  return entries[0].timestamp;
}

/**
 * Format a Date as local wall-clock time (e.g., "2:35 PM" or "14:35").
 * Respects the user's browser locale for 12h/24h format.
 */
export function formatLocalTime(date: Date): string {
  return date.toLocaleTimeString([], {
    hour: "numeric",
    minute: "2-digit",
  });
}

/**
 * Default grouping window in milliseconds.
 * Consecutive transcript entries from the same speaker within this window
 * are merged into a single displayed message.
 */
export const GROUPING_WINDOW_MS = 2000;

export interface TranscriptEntry {
  id: string;
  speaker: "user" | "agent" | "user-text" | "system";
  text: string;
  timestamp: Date;
}

export interface GroupedTranscriptEntry {
  ids: string[];
  speaker: "user" | "agent" | "user-text" | "system";
  text: string;
  timestamp: Date;
  lastTimestamp: Date;
}

/**
 * Group consecutive transcript entries from the same speaker when
 * the time gap between them is below the given window.
 */
export function groupTranscriptEntries(
  entries: TranscriptEntry[],
  windowMs: number = GROUPING_WINDOW_MS,
): GroupedTranscriptEntry[] {
  if (entries.length === 0) return [];

  const groups: GroupedTranscriptEntry[] = [];

  for (const entry of entries) {
    const last = groups[groups.length - 1];
    if (
      last &&
      last.speaker === entry.speaker &&
      entry.speaker !== "system" &&
      entry.timestamp.getTime() - last.lastTimestamp.getTime() < windowMs
    ) {
      last.ids.push(entry.id);
      last.text += " " + entry.text;
      last.lastTimestamp = entry.timestamp;
    } else {
      groups.push({
        ids: [entry.id],
        speaker: entry.speaker,
        text: entry.text,
        timestamp: entry.timestamp,
        lastTimestamp: entry.timestamp,
      });
    }
  }

  return groups;
}
