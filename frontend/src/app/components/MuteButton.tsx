"use client";

import { useEffect, useCallback } from "react";
import { useLocalParticipant } from "@livekit/components-react";

/**
 * MuteButton — toggles user microphone on/off during a LiveKit call.
 *
 * Uses LiveKit's `useLocalParticipant()` to read and control mic state.
 * Supports keyboard shortcut (M key) when no text input is focused.
 */
export function MuteButton() {
  const { localParticipant, isMicrophoneEnabled } = useLocalParticipant();

  const toggleMute = useCallback(() => {
    localParticipant.setMicrophoneEnabled(!isMicrophoneEnabled);
  }, [localParticipant, isMicrophoneEnabled]);

  // Global keyboard shortcut: M to toggle mute
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== "m" && e.key !== "M") return;

      // Don't toggle when user is typing in an input or textarea
      const active = document.activeElement;
      const tagName = active?.tagName?.toUpperCase();
      if (tagName === "INPUT" || tagName === "TEXTAREA") return;

      toggleMute();
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [toggleMute]);

  const label = isMicrophoneEnabled ? "Mute microphone (M)" : "Unmute microphone (M)";

  return (
    <button
      onClick={toggleMute}
      aria-label={label}
      title={label}
      style={{
        width: "48px",
        height: "48px",
        borderRadius: "50%",
        border: `2px solid ${isMicrophoneEnabled ? "#22c55e" : "#ef4444"}`,
        borderColor: isMicrophoneEnabled ? "#22c55e" : "#ef4444",
        background: isMicrophoneEnabled ? "transparent" : "rgba(239, 68, 68, 0.15)",
        color: isMicrophoneEnabled ? "#e2e8f0" : "#ef4444",
        cursor: "pointer",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: "1.3rem",
        lineHeight: 1,
        transition: "all 0.15s ease",
      }}
    >
      {isMicrophoneEnabled ? "\u{1F3A4}" : "\u{1F507}"}
    </button>
  );
}
