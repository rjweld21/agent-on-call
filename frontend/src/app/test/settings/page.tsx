"use client";

import { useState } from "react";
import { SettingsProvider } from "@/lib/settings-context";
import { SettingsPanel } from "@/app/components/SettingsPanel";

/**
 * Test page for settings panel E2E testing.
 * Renders the settings button and panel without requiring LiveKit.
 */
export default function SettingsTestPage() {
  const [settingsOpen, setSettingsOpen] = useState(false);

  return (
    <SettingsProvider>
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
        <h1 style={{ fontSize: "2rem", fontWeight: "bold" }}>Settings Test Page</h1>
        <p style={{ color: "#94a3b8" }}>
          Click the button below to open the settings panel.
        </p>
        <button
          data-testid="settings-button"
          onClick={() => setSettingsOpen(true)}
          aria-label="Open settings"
          style={{
            background: "none",
            border: "1px solid #334155",
            borderRadius: "8px",
            color: "#94a3b8",
            cursor: "pointer",
            fontSize: "1.5rem",
            padding: "0.5rem 1rem",
          }}
        >
          &#9881; Open Settings
        </button>

        <SettingsPanel isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />
      </div>
    </SettingsProvider>
  );
}
