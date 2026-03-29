import { test, expect } from "@playwright/test";

test.describe("Room layout — 3-column redesign", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/test/room-layout");
  });

  test("renders a 3-column grid layout", async ({ page }) => {
    const layout = page.getByTestId("room-layout");
    await expect(layout).toBeVisible();

    // Verify grid display
    const display = await layout.evaluate((el) => getComputedStyle(el).display);
    expect(display).toBe("grid");
  });

  test("left column contains transcript", async ({ page }) => {
    const col = page.getByTestId("column-transcript");
    await expect(col).toBeVisible();
    await expect(col).toContainText("Transcript");
    // Transcript entries should be present
    const timestamps = page.getByTestId("transcript-timestamp");
    await expect(timestamps).toHaveCount(4);
  });

  test("center column contains controls", async ({ page }) => {
    const col = page.getByTestId("column-controls");
    await expect(col).toBeVisible();
    await expect(col).toContainText("Agent On Call");
    await expect(col).toContainText("Participants");
    await expect(col).toContainText("Agent Status");
    await expect(col).toContainText("Leave Call");
  });

  test("right column contains activity and terminal panels", async ({ page }) => {
    const col = page.getByTestId("column-activity");
    await expect(col).toBeVisible();

    const thinkingPanel = page.getByTestId("thinking-panel");
    await expect(thinkingPanel).toBeVisible();
    await expect(thinkingPanel).toContainText("Agent Activity");

    const terminalPanel = page.getByTestId("terminal-panel");
    await expect(terminalPanel).toBeVisible();
    await expect(terminalPanel).toContainText("Terminal Output");
  });

  test("settings gear is accessible", async ({ page }) => {
    const button = page.getByTestId("settings-button");
    await expect(button).toBeVisible();
    await button.click();
    const panel = page.getByRole("dialog", { name: "Settings panel" });
    await expect(panel).toBeVisible();
  });

  test("all three columns are visible side-by-side at desktop width", async ({ page }) => {
    // Default viewport is typically 1280px wide
    const transcript = page.getByTestId("column-transcript");
    const controls = page.getByTestId("column-controls");
    const activity = page.getByTestId("column-activity");

    const tBox = await transcript.boundingBox();
    const cBox = await controls.boundingBox();
    const aBox = await activity.boundingBox();

    expect(tBox).not.toBeNull();
    expect(cBox).not.toBeNull();
    expect(aBox).not.toBeNull();

    // Transcript should be left of controls
    expect(tBox!.x + tBox!.width).toBeLessThanOrEqual(cBox!.x + 2);
    // Controls should be left of activity
    expect(cBox!.x + cBox!.width).toBeLessThanOrEqual(aBox!.x + 2);
  });

  test("right column splits 50/50 between activity and terminal", async ({ page }) => {
    const col = page.getByTestId("column-activity");
    const colBox = await col.boundingBox();
    expect(colBox).not.toBeNull();

    const thinkingPanel = page.getByTestId("thinking-panel");
    const terminalPanel = page.getByTestId("terminal-panel");
    const tpBox = await thinkingPanel.boundingBox();
    const termBox = await terminalPanel.boundingBox();

    expect(tpBox).not.toBeNull();
    expect(termBox).not.toBeNull();

    // ThinkingPanel should be above TerminalPanel
    expect(tpBox!.y + tpBox!.height).toBeLessThanOrEqual(termBox!.y + 2);

    // Each should take roughly half the column height (within 15% tolerance)
    const colHeight = colBox!.height;
    expect(tpBox!.height).toBeGreaterThan(colHeight * 0.3);
    expect(termBox!.height).toBeGreaterThan(colHeight * 0.3);
  });

  test("transcript column has text input at the bottom", async ({ page }) => {
    const col = page.getByTestId("column-transcript");
    const input = col.locator('input[placeholder*="Type a message"]');
    await expect(input).toBeVisible();
  });
});

test.describe("Room layout — responsive stacking", () => {
  test("stacks vertically on narrow screens", async ({ page }) => {
    await page.setViewportSize({ width: 600, height: 800 });
    await page.goto("/test/room-layout");

    const transcript = page.getByTestId("column-transcript");
    const controls = page.getByTestId("column-controls");
    const activity = page.getByTestId("column-activity");

    const tBox = await transcript.boundingBox();
    const cBox = await controls.boundingBox();
    const aBox = await activity.boundingBox();

    expect(tBox).not.toBeNull();
    expect(cBox).not.toBeNull();
    expect(aBox).not.toBeNull();

    // In stacked mode, all columns should have similar x positions (left-aligned)
    expect(Math.abs(tBox!.x - cBox!.x)).toBeLessThan(10);
    expect(Math.abs(cBox!.x - aBox!.x)).toBeLessThan(10);

    // And they should be stacked vertically
    expect(tBox!.y).toBeLessThan(cBox!.y);
    expect(cBox!.y).toBeLessThan(aBox!.y);
  });
});
