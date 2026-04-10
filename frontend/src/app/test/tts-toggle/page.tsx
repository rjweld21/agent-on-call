"use client";

import { SettingsProvider } from "@/lib/settings-context";
import { TtsToggle, useTtsToggle } from "@/app/components/TtsToggle";

/**
 * Test page for TTS toggle E2E testing.
 * Renders the TTS toggle button without requiring LiveKit.
 */
function TtsToggleTestContent() {
  const { ttsEnabled, setTtsEnabled } = useTtsToggle();

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        height: "100vh",
        gap: "1.5rem",
        background: "#0f172a",
        fontFamily: "system-ui, sans-serif",
        color: "#e2e8f0",
      }}
    >
      <h1 style={{ fontSize: "2rem", fontWeight: "bold" }}>TTS Toggle Test Page</h1>
      <p style={{ color: "#94a3b8" }}>
        Use the toggle button or press V to toggle TTS on/off.
      </p>

      <TtsToggle />

      <p data-testid="tts-state" style={{ color: "#94a3b8", fontSize: "1rem" }}>
        TTS is currently: <strong>{ttsEnabled ? "ON" : "OFF"}</strong>
      </p>

      {/* Simulate auto-disable from agent */}
      <button
        data-testid="simulate-auto-disable"
        onClick={() => setTtsEnabled(false)}
        style={{
          padding: "0.5rem 1rem",
          borderRadius: "8px",
          border: "1px solid #334155",
          background: "#1e293b",
          color: "#94a3b8",
          cursor: "pointer",
          fontSize: "0.85rem",
        }}
      >
        Simulate TTS Auto-Disable
      </button>

      {/* Text input to test keyboard shortcut ignoring */}
      <input
        data-testid="test-input"
        type="text"
        placeholder="Type here to test V key ignoring..."
        style={{
          padding: "0.5rem",
          background: "#1e293b",
          border: "1px solid #334155",
          borderRadius: "8px",
          color: "#e2e8f0",
          width: "300px",
        }}
      />
    </div>
  );
}

export default function TtsToggleTestPage() {
  return (
    <SettingsProvider>
      <TtsToggleTestContent />
    </SettingsProvider>
  );
}
