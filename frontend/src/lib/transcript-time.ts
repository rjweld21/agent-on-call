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
