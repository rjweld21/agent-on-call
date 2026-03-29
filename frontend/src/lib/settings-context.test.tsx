import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, act } from "@testing-library/react";
import { SettingsProvider, useSettings, DEFAULT_SETTINGS } from "./settings-context";

function TestConsumer() {
  const { settings, updateSetting } = useSettings();
  return (
    <div>
      <span data-testid="settings">{JSON.stringify(settings)}</span>
      <button
        data-testid="update-btn"
        onClick={() => updateSetting("general", "theme", "light")}
      >
        Update
      </button>
    </div>
  );
}

describe("SettingsProvider", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("provides default settings when localStorage is empty", () => {
    render(
      <SettingsProvider>
        <TestConsumer />
      </SettingsProvider>,
    );
    const settingsText = screen.getByTestId("settings").textContent;
    expect(JSON.parse(settingsText!)).toEqual(DEFAULT_SETTINGS);
  });

  it("loads settings from localStorage after mount", async () => {
    const stored = {
      ...DEFAULT_SETTINGS,
      general: { ...DEFAULT_SETTINGS.general, theme: "light" },
    };
    localStorage.setItem("aoc-settings", JSON.stringify(stored));

    render(
      <SettingsProvider>
        <TestConsumer />
      </SettingsProvider>,
    );

    // After useEffect hydration, picks up localStorage values
    await act(async () => {});
    const settingsText = screen.getByTestId("settings").textContent;
    expect(JSON.parse(settingsText!).general.theme).toBe("light");
  });

  it("falls back to defaults when localStorage has invalid JSON", () => {
    localStorage.setItem("aoc-settings", "not-valid-json");

    render(
      <SettingsProvider>
        <TestConsumer />
      </SettingsProvider>,
    );
    const settingsText = screen.getByTestId("settings").textContent;
    expect(JSON.parse(settingsText!)).toEqual(DEFAULT_SETTINGS);
  });

  it("persists settings to localStorage when updated", async () => {
    render(
      <SettingsProvider>
        <TestConsumer />
      </SettingsProvider>,
    );

    await act(async () => {
      screen.getByTestId("update-btn").click();
    });

    const stored = JSON.parse(localStorage.getItem("aoc-settings")!);
    expect(stored.general.theme).toBe("light");
  });

  it("updates settings state when updateSetting is called", async () => {
    render(
      <SettingsProvider>
        <TestConsumer />
      </SettingsProvider>,
    );

    await act(async () => {
      screen.getByTestId("update-btn").click();
    });

    const settingsText = screen.getByTestId("settings").textContent;
    expect(JSON.parse(settingsText!).general.theme).toBe("light");
  });
});

describe("useSettings", () => {
  it("throws when used outside SettingsProvider", () => {
    // Suppress console.error for this test
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});
    expect(() => render(<TestConsumer />)).toThrow(
      "useSettings must be used within a SettingsProvider",
    );
    spy.mockRestore();
  });
});
