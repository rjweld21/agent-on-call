import { test, expect } from "@playwright/test";

test.describe("Data channel message handling", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/test/data-channel");
    await expect(page.getByTestId("data-channel-test-page")).toBeVisible();
  });

  test("agent_action events render in ThinkingPanel", async ({ page }) => {
    // Initially no activities
    await expect(page.getByTestId("activity-count")).toHaveText("0");
    await expect(page.getByTestId("thinking-empty")).toBeVisible();

    // Send an agent_action
    await page.getByTestId("btn-agent-action").click();

    // Activity should appear in ThinkingPanel
    await expect(page.getByTestId("activity-count")).toHaveText("1");
    const activityItem = page.getByTestId("activity-item");
    await expect(activityItem).toHaveCount(1);
    await expect(activityItem).toContainText("Analyzing the user request...");

    // Send another action
    await page.getByTestId("btn-agent-action").click();
    await expect(page.getByTestId("activity-count")).toHaveText("2");
    await expect(page.getByTestId("activity-item")).toHaveCount(2);
  });

  test("command_output events render in TerminalPanel with actual command text", async ({ page }) => {
    // Initially no terminal entries
    await expect(page.getByTestId("terminal-count")).toHaveText("0");

    // Send a command_output event (triggers agent_action + command_output)
    await page.getByTestId("btn-command-output").click();

    // Wait for the terminal entry to appear (command_output arrives after 100ms delay)
    await expect(page.getByTestId("terminal-count")).toHaveText("1", { timeout: 2000 });

    // Verify the command text is the actual command, not a summary
    const terminalCommand = page.getByTestId("terminal-command");
    await expect(terminalCommand).toHaveCount(1);
    await expect(terminalCommand).toContainText("ls -la /tmp");

    // Verify the output is present
    const terminalOutput = page.getByTestId("terminal-output");
    await expect(terminalOutput).toContainText("total 0");

    // Verify the activity panel also shows the action
    await expect(page.getByTestId("activity-count")).toHaveText("1");
  });

  test("tts_status events show/hide banner", async ({ page }) => {
    // No banner initially
    await expect(page.getByTestId("tts-status")).toHaveText("none");
    await expect(page.getByTestId("tts-banner")).not.toBeVisible();

    // Send TTS unavailable
    await page.getByTestId("btn-tts-unavailable").click();

    // Banner should appear
    await expect(page.getByTestId("tts-banner")).toBeVisible();
    await expect(page.getByTestId("tts-banner")).toContainText("TTS unavailable: TTS service quota exceeded");
    await expect(page.getByTestId("tts-status")).toContainText("unavailable");

    // Send TTS available again
    await page.getByTestId("btn-tts-available").click();

    // Banner should disappear
    await expect(page.getByTestId("tts-banner")).not.toBeVisible();
    await expect(page.getByTestId("tts-status")).toHaveText("none");
  });

  test("malformed messages handled gracefully (no crash)", async ({ page }) => {
    // Send a malformed message
    await page.getByTestId("btn-malformed").click();

    // Page should still be responsive — check the indicator
    await expect(page.getByTestId("malformed-handled")).toBeVisible();
    await expect(page.getByTestId("malformed-handled")).toContainText("no crash");

    // Verify panels are still functional after malformed message
    await page.getByTestId("btn-agent-action").click();
    await expect(page.getByTestId("activity-count")).toHaveText("1");

    await page.getByTestId("btn-tts-unavailable").click();
    await expect(page.getByTestId("tts-banner")).toBeVisible();
  });

  test("test page simulates data channel messages without LiveKit connection", async ({ page }) => {
    // Verify the page renders without errors — no connection failures
    await expect(page.getByTestId("data-channel-test-page")).toBeVisible();

    // All control buttons should be visible and clickable
    await expect(page.getByTestId("btn-agent-action")).toBeVisible();
    await expect(page.getByTestId("btn-command-output")).toBeVisible();
    await expect(page.getByTestId("btn-tts-unavailable")).toBeVisible();
    await expect(page.getByTestId("btn-tts-available")).toBeVisible();
    await expect(page.getByTestId("btn-malformed")).toBeVisible();

    // Both panels render correctly without LiveKit
    await expect(page.getByTestId("thinking-panel")).toBeVisible();
    await expect(page.getByTestId("terminal-panel")).toBeVisible();

    // Status counters are at zero (no pre-loaded data)
    await expect(page.getByTestId("activity-count")).toHaveText("0");
    await expect(page.getByTestId("terminal-count")).toHaveText("0");
    await expect(page.getByTestId("tts-status")).toHaveText("none");
  });

  test("multiple rapid messages are processed correctly", async ({ page }) => {
    // Send multiple actions rapidly
    await page.getByTestId("btn-agent-action").click();
    await page.getByTestId("btn-agent-action").click();
    await page.getByTestId("btn-agent-action").click();

    // All should be tracked
    await expect(page.getByTestId("activity-count")).toHaveText("3");
    await expect(page.getByTestId("activity-item")).toHaveCount(3);
  });
});
