import { test, expect } from "@playwright/test";

test.describe("TTS Toggle", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/test/tts-toggle");
  });

  test("toggle button is visible and shows TTS as ON by default", async ({ page }) => {
    const toggle = page.getByTestId("tts-toggle");
    await expect(toggle).toBeVisible();
    await expect(toggle).toHaveAttribute("aria-label", "Disable voice (V)");
    await expect(page.getByTestId("tts-state")).toContainText("ON");
  });

  test("clicking toggle switches TTS off", async ({ page }) => {
    await page.getByTestId("tts-toggle").click();
    await expect(page.getByTestId("tts-state")).toContainText("OFF");
    await expect(page.getByTestId("tts-toggle")).toHaveAttribute(
      "aria-label",
      "Enable voice (V)",
    );
  });

  test("clicking toggle twice returns to ON", async ({ page }) => {
    await page.getByTestId("tts-toggle").click();
    await expect(page.getByTestId("tts-state")).toContainText("OFF");
    await page.getByTestId("tts-toggle").click();
    await expect(page.getByTestId("tts-state")).toContainText("ON");
  });

  test("V keyboard shortcut toggles TTS off", async ({ page }) => {
    // Click on the page body first to ensure it has focus (not an input)
    await page.locator("body").click();
    await page.keyboard.press("v");
    await expect(page.getByTestId("tts-state")).toContainText("OFF");
  });

  test("V keyboard shortcut does not toggle when input is focused", async ({ page }) => {
    await page.getByTestId("test-input").focus();
    await page.keyboard.press("v");
    // Should still be ON because input is focused
    await expect(page.getByTestId("tts-state")).toContainText("ON");
  });

  test("auto-disable simulation sets toggle to off", async ({ page }) => {
    await expect(page.getByTestId("tts-state")).toContainText("ON");
    await page.getByTestId("simulate-auto-disable").click();
    await expect(page.getByTestId("tts-state")).toContainText("OFF");
  });

  test("TTS state persists across page reloads", async ({ page }) => {
    // Toggle off
    await page.getByTestId("tts-toggle").click();
    await expect(page.getByTestId("tts-state")).toContainText("OFF");

    // Reload
    await page.reload();
    await expect(page.getByTestId("tts-state")).toContainText("OFF");
  });

  test("toggle has correct visual styling when ON (green border)", async ({ page }) => {
    const toggle = page.getByTestId("tts-toggle");
    const borderColor = await toggle.evaluate(
      (el) => (el as HTMLElement).style.borderColor,
    );
    expect(borderColor).toMatch(/22c55e|rgb\(34,\s*197,\s*94\)/);
  });

  test("toggle has correct visual styling when OFF (red border)", async ({ page }) => {
    await page.getByTestId("tts-toggle").click();
    const toggle = page.getByTestId("tts-toggle");
    const borderColor = await toggle.evaluate(
      (el) => (el as HTMLElement).style.borderColor,
    );
    expect(borderColor).toMatch(/ef4444|rgb\(239,\s*68,\s*68\)/);
  });
});
