import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TtsToggle, useTtsToggle } from "./TtsToggle";
import { SettingsProvider, useSettings } from "@/lib/settings-context";

function renderWithProvider(ui: React.ReactElement) {
  return render(<SettingsProvider>{ui}</SettingsProvider>);
}

describe("TtsToggle", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders with TTS enabled (default state)", () => {
    renderWithProvider(<TtsToggle />);
    const button = screen.getByRole("button", { name: /disable voice/i });
    expect(button).toBeInTheDocument();
  });

  it("shows correct aria-label when TTS is enabled", () => {
    renderWithProvider(<TtsToggle />);
    expect(screen.getByRole("button", { name: "Disable voice (V)" })).toBeInTheDocument();
  });

  it("toggles TTS off on click", async () => {
    renderWithProvider(<TtsToggle />);
    const button = screen.getByTestId("tts-toggle");
    await userEvent.click(button);
    expect(screen.getByRole("button", { name: "Enable voice (V)" })).toBeInTheDocument();
  });

  it("toggles TTS back on with second click", async () => {
    renderWithProvider(<TtsToggle />);
    const button = screen.getByTestId("tts-toggle");
    await userEvent.click(button);
    expect(screen.getByRole("button", { name: "Enable voice (V)" })).toBeInTheDocument();
    await userEvent.click(button);
    expect(screen.getByRole("button", { name: "Disable voice (V)" })).toBeInTheDocument();
  });

  it("has green border when TTS is enabled", () => {
    renderWithProvider(<TtsToggle />);
    const button = screen.getByTestId("tts-toggle");
    expect(button.style.borderColor).toMatch(/22c55e|rgb\(34,\s*197,\s*94\)/);
  });

  it("has red border when TTS is disabled", async () => {
    renderWithProvider(<TtsToggle />);
    const button = screen.getByTestId("tts-toggle");
    await userEvent.click(button);
    expect(button.style.borderColor).toMatch(/ef4444|rgb\(239,\s*68,\s*68\)/);
  });

  it("toggles TTS on V key press", async () => {
    renderWithProvider(<TtsToggle />);
    expect(screen.getByRole("button", { name: "Disable voice (V)" })).toBeInTheDocument();
    fireEvent.keyDown(document, { key: "v" });
    expect(screen.getByRole("button", { name: "Enable voice (V)" })).toBeInTheDocument();
  });

  it("toggles TTS on uppercase V key press", async () => {
    renderWithProvider(<TtsToggle />);
    expect(screen.getByRole("button", { name: "Disable voice (V)" })).toBeInTheDocument();
    fireEvent.keyDown(document, { key: "V" });
    expect(screen.getByRole("button", { name: "Enable voice (V)" })).toBeInTheDocument();
  });

  it("does NOT toggle when V is pressed while typing in an input", () => {
    renderWithProvider(
      <div>
        <input data-testid="text-input" />
        <TtsToggle />
      </div>,
    );
    const input = screen.getByTestId("text-input");
    input.focus();
    fireEvent.keyDown(document, { key: "v" });
    // Should still show as enabled (no toggle)
    expect(screen.getByRole("button", { name: "Disable voice (V)" })).toBeInTheDocument();
  });

  it("does NOT toggle when V is pressed while typing in a textarea", () => {
    renderWithProvider(
      <div>
        <textarea data-testid="text-area" />
        <TtsToggle />
      </div>,
    );
    const textarea = screen.getByTestId("text-area");
    textarea.focus();
    fireEvent.keyDown(document, { key: "v" });
    expect(screen.getByRole("button", { name: "Disable voice (V)" })).toBeInTheDocument();
  });

  it("persists TTS state to localStorage", async () => {
    renderWithProvider(<TtsToggle />);
    await userEvent.click(screen.getByTestId("tts-toggle"));
    const stored = JSON.parse(localStorage.getItem("aoc-settings")!);
    expect(stored.voice.ttsEnabled).toBe(false);
  });

  it("loads persisted TTS-off state from localStorage", async () => {
    const stored = {
      general: {},
      model: {},
      voice: { ttsEnabled: false },
    };
    localStorage.setItem("aoc-settings", JSON.stringify(stored));

    renderWithProvider(<TtsToggle />);
    // After hydration from localStorage
    await act(async () => {});
    expect(screen.getByRole("button", { name: "Enable voice (V)" })).toBeInTheDocument();
  });
});

// Test the useTtsToggle hook
function TtsToggleHookConsumer() {
  const { ttsEnabled, setTtsEnabled } = useTtsToggle();
  return (
    <div>
      <span data-testid="tts-state">{ttsEnabled ? "on" : "off"}</span>
      <button data-testid="force-off" onClick={() => setTtsEnabled(false)}>
        Force Off
      </button>
      <button data-testid="force-on" onClick={() => setTtsEnabled(true)}>
        Force On
      </button>
    </div>
  );
}

describe("useTtsToggle", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("returns ttsEnabled=true by default", () => {
    renderWithProvider(<TtsToggleHookConsumer />);
    expect(screen.getByTestId("tts-state").textContent).toBe("on");
  });

  it("setTtsEnabled(false) disables TTS", async () => {
    renderWithProvider(<TtsToggleHookConsumer />);
    await userEvent.click(screen.getByTestId("force-off"));
    expect(screen.getByTestId("tts-state").textContent).toBe("off");
  });

  it("setTtsEnabled(true) enables TTS", async () => {
    renderWithProvider(<TtsToggleHookConsumer />);
    await userEvent.click(screen.getByTestId("force-off"));
    expect(screen.getByTestId("tts-state").textContent).toBe("off");
    await userEvent.click(screen.getByTestId("force-on"));
    expect(screen.getByTestId("tts-state").textContent).toBe("on");
  });
});
