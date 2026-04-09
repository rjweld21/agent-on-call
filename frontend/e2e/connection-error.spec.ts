import { test, expect } from "@playwright/test";

test.describe("Connection error states", () => {
  test("shows error banner when server is unreachable", async ({ page }) => {
    // Intercept the token API call and make it fail (simulating unreachable server)
    await page.route("**/api/token**", (route) =>
      route.abort("connectionrefused")
    );

    await page.goto("/");

    // Click "Start Call"
    const startButton = page.getByTestId("start-call-button");
    await expect(startButton).toBeVisible();
    await startButton.click();

    // Error banner should appear
    const errorBanner = page.getByTestId("connection-error");
    await expect(errorBanner).toBeVisible({ timeout: 5000 });

    // Error message should be descriptive
    const errorMessage = page.getByTestId("error-message");
    await expect(errorMessage).toBeVisible();
    const messageText = await errorMessage.textContent();
    expect(messageText).toBeTruthy();
    expect(messageText!.length).toBeGreaterThan(5);
  });

  test("shows retry button on error", async ({ page }) => {
    await page.route("**/api/token**", (route) =>
      route.abort("connectionrefused")
    );

    await page.goto("/");
    await page.getByTestId("start-call-button").click();

    // Wait for error state
    await expect(page.getByTestId("connection-error")).toBeVisible({ timeout: 5000 });

    // Retry button should be visible
    const retryButton = page.getByTestId("retry-button");
    await expect(retryButton).toBeVisible();
    await expect(retryButton).toHaveText("Retry");
  });

  test("dismiss button returns to home screen", async ({ page }) => {
    await page.route("**/api/token**", (route) =>
      route.abort("connectionrefused")
    );

    await page.goto("/");
    await page.getByTestId("start-call-button").click();

    // Wait for error
    await expect(page.getByTestId("connection-error")).toBeVisible({ timeout: 5000 });

    // Click dismiss
    await page.getByTestId("dismiss-error-button").click();

    // Should return to home screen with Start Call button
    await expect(page.getByTestId("connection-error")).not.toBeVisible();
    await expect(page.getByTestId("start-call-button")).toBeVisible();
  });

  test("retry button attempts reconnection", async ({ page }) => {
    let callCount = 0;
    await page.route("**/api/token**", (route) => {
      callCount++;
      if (callCount <= 2) {
        return route.abort("connectionrefused");
      }
      // Third attempt succeeds (but with invalid token so we won't actually connect to LiveKit)
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ token: "test-token", url: "wss://test.example.com" }),
      });
    });

    await page.goto("/");
    await page.getByTestId("start-call-button").click();

    // First attempt fails
    await expect(page.getByTestId("connection-error")).toBeVisible({ timeout: 5000 });
    expect(callCount).toBe(1);

    // Retry — second attempt also fails
    await page.getByTestId("retry-button").click();
    await expect(page.getByTestId("connection-error")).toBeVisible({ timeout: 5000 });
    expect(callCount).toBe(2);

    // Retry again — third attempt succeeds, error should disappear
    await page.getByTestId("retry-button").click();
    await expect(page.getByTestId("connection-error")).not.toBeVisible({ timeout: 5000 });
    expect(callCount).toBe(3);
  });

  test("shows error for HTTP error responses", async ({ page }) => {
    await page.route("**/api/token**", (route) =>
      route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ error: "Internal server error" }),
      })
    );

    await page.goto("/");
    await page.getByTestId("start-call-button").click();

    // Error should show server status
    await expect(page.getByTestId("connection-error")).toBeVisible({ timeout: 5000 });
    const errorMessage = page.getByTestId("error-message");
    await expect(errorMessage).toContainText("500");
  });

  test("shows error for invalid server response (missing token)", async ({ page }) => {
    await page.route("**/api/token**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ url: "wss://test.example.com" }),
      })
    );

    await page.goto("/");
    await page.getByTestId("start-call-button").click();

    await expect(page.getByTestId("connection-error")).toBeVisible({ timeout: 5000 });
    await expect(page.getByTestId("error-message")).toContainText("missing token");
  });
});
