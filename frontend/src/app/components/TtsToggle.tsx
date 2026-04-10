"use client";

import { useEffect, useCallback } from "react";
import { useSettings } from "@/lib/settings-context";

/**
 * TtsToggle — toggles TTS (text-to-speech) on/off during a call.
 *
 * Uses the settings context to persist state in localStorage and sync
 * the toggle state to the agent via data channel. Shows a speaker icon
 * with a strikethrough when TTS is off.
 *
 * Supports keyboard shortcut (V key) when no text input is focused.
 */
export function TtsToggle() {
  const { settings, updateSetting } = useSettings();
  const ttsEnabled = (settings.voice?.ttsEnabled as boolean) ?? true;

  const toggleTts = useCallback(() => {
    updateSetting("voice", "ttsEnabled", !ttsEnabled);
  }, [updateSetting, ttsEnabled]);

  /**
   * Set TTS enabled state directly (used for external sync,
   * e.g., when TTS is auto-disabled due to API errors).
   */
  const setTtsEnabled = useCallback(
    (enabled: boolean) => {
      updateSetting("voice", "ttsEnabled", enabled);
    },
    [updateSetting],
  );

  // Global keyboard shortcut: V to toggle TTS
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== "v" && e.key !== "V") return;

      // Don't toggle when user is typing in an input or textarea
      const active = document.activeElement;
      const tagName = active?.tagName?.toUpperCase();
      if (tagName === "INPUT" || tagName === "TEXTAREA") return;

      toggleTts();
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [toggleTts]);

  const label = ttsEnabled ? "Disable voice (V)" : "Enable voice (V)";

  return (
    <button
      onClick={toggleTts}
      aria-label={label}
      title={label}
      data-testid="tts-toggle"
      style={{
        width: "48px",
        height: "48px",
        borderRadius: "50%",
        border: `2px solid ${ttsEnabled ? "#22c55e" : "#ef4444"}`,
        borderColor: ttsEnabled ? "#22c55e" : "#ef4444",
        background: ttsEnabled ? "transparent" : "rgba(239, 68, 68, 0.15)",
        color: ttsEnabled ? "#e2e8f0" : "#ef4444",
        cursor: "pointer",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: "1.3rem",
        lineHeight: 1,
        transition: "all 0.15s ease",
      }}
    >
      {ttsEnabled ? "\uD83D\uDD0A" : "\uD83D\uDD07"}
    </button>
  );
}

/**
 * Hook to expose TTS toggle state and setter for external sync.
 * Used by page.tsx to sync TTS toggle when TTS is auto-disabled.
 */
export function useTtsToggle() {
  const { settings, updateSetting } = useSettings();
  const ttsEnabled = (settings.voice?.ttsEnabled as boolean) ?? true;

  const setTtsEnabled = useCallback(
    (enabled: boolean) => {
      updateSetting("voice", "ttsEnabled", enabled);
    },
    [updateSetting],
  );

  return { ttsEnabled, setTtsEnabled };
}
