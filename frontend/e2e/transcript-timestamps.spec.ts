import { test, expect } from "@playwright/test";

test.describe("Transcript timestamps", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/test/transcript");
  });

  test("displays timestamps in HH:MM:SS format", async ({ page }) => {
    const timestamps = page.getByTestId("transcript-timestamp");
    await expect(timestamps).toHaveCount(5);

    // First entry should be 00:00:00 (session start)
    await expect(timestamps.nth(0)).toHaveText("00:00:00");

    // Second entry at +5s
    await expect(timestamps.nth(1)).toHaveText("00:00:05");

    // Third entry at +15s
    await expect(timestamps.nth(2)).toHaveText("00:00:15");

    // Fourth entry at +105s = 1:45
    await expect(timestamps.nth(3)).toHaveText("00:01:45");

    // Fifth entry at +110s = 1:50
    await expect(timestamps.nth(4)).toHaveText("00:01:50");
  });

  test("timestamps are visible and styled with monospace font", async ({ page }) => {
    const firstTimestamp = page.getByTestId("transcript-timestamp").first();
    await expect(firstTimestamp).toBeVisible();

    const fontFamily = await firstTimestamp.evaluate(
      (el) => getComputedStyle(el).fontFamily,
    );
    expect(fontFamily).toContain("monospace");
  });

  test("shows pause gap indicator for gaps > 60 seconds", async ({ page }) => {
    const gaps = page.getByTestId("gap-indicator");
    // There should be exactly 1 gap indicator (90s gap between entries 3 and 4)
    await expect(gaps).toHaveCount(1);
    await expect(gaps.first()).toContainText("1 min gap");
  });

  test("no gap indicator for gaps <= 60 seconds", async ({ page }) => {
    // Only 1 gap indicator total, meaning the short gaps don't produce indicators
    const gaps = page.getByTestId("gap-indicator");
    await expect(gaps).toHaveCount(1);
  });

  test("transcript container renders all entries", async ({ page }) => {
    const container = page.getByTestId("transcript-container");
    await expect(container).toBeVisible();

    // Verify all speaker labels are present
    await expect(container).toContainText("You:");
    await expect(container).toContainText("Agent:");
    await expect(container).toContainText("You (text):");
  });
});
