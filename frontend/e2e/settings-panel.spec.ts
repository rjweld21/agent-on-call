import { test, expect } from "@playwright/test";

test.describe("Settings panel", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/test/settings");
  });

  test("settings button is visible", async ({ page }) => {
    const button = page.getByTestId("settings-button");
    await expect(button).toBeVisible();
    await expect(button).toHaveAttribute("aria-label", "Open settings");
  });

  test("clicking settings button opens the panel", async ({ page }) => {
    await page.getByTestId("settings-button").click();
    const panel = page.getByRole("dialog", { name: "Settings panel" });
    await expect(panel).toBeVisible();
    await expect(panel).toContainText("Settings");
  });

  test("panel shows section titles", async ({ page }) => {
    await page.getByTestId("settings-button").click();
    const panel = page.getByRole("dialog", { name: "Settings panel" });
    await expect(panel).toContainText("Model");
    await expect(panel).toContainText("Voice");
  });

  test("close button closes the panel", async ({ page }) => {
    await page.getByTestId("settings-button").click();
    await expect(page.getByRole("dialog")).toBeVisible();

    await page.getByLabel("Close settings").click();
    await expect(page.getByRole("dialog")).not.toBeVisible();
  });

  test("clicking backdrop closes the panel", async ({ page }) => {
    await page.getByTestId("settings-button").click();
    await expect(page.getByRole("dialog")).toBeVisible();

    await page.getByTestId("settings-backdrop").click();
    await expect(page.getByRole("dialog")).not.toBeVisible();
  });

  test("pressing Escape closes the panel", async ({ page }) => {
    await page.getByTestId("settings-button").click();
    await expect(page.getByRole("dialog")).toBeVisible();

    await page.keyboard.press("Escape");
    await expect(page.getByRole("dialog")).not.toBeVisible();
  });

  test("panel can be reopened after closing", async ({ page }) => {
    // Open
    await page.getByTestId("settings-button").click();
    await expect(page.getByRole("dialog")).toBeVisible();

    // Close
    await page.keyboard.press("Escape");
    await expect(page.getByRole("dialog")).not.toBeVisible();

    // Reopen
    await page.getByTestId("settings-button").click();
    await expect(page.getByRole("dialog")).toBeVisible();
  });
});
