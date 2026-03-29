"use client";

import { useSettings } from "@/lib/settings-context";

export const VERBOSITY_LEVELS = [
  {
    level: 1,
    name: "Concise",
    prompt:
      "Be extremely concise. Give bare minimum answers. Short, declarative sentences. Skip pleasantries, context, and elaboration.",
  },
  {
    level: 2,
    name: "Brief",
    prompt:
      "Be brief but complete. Answer with just enough context. No filler or examples unless asked. One or two sentences when possible.",
  },
  {
    level: 3,
    name: "Balanced",
    prompt:
      "Use a natural conversational tone. Provide context when helpful. Explain reasoning briefly. This is the default voice.",
  },
  {
    level: 4,
    name: "Detailed",
    prompt:
      "Give thorough explanations. Walk through reasoning step by step. Offer examples and alternatives. Good for learning.",
  },
  {
    level: 5,
    name: "Verbose",
    prompt:
      "Explain everything in full detail. Cover background, context, trade-offs, edge cases, and implications. Almost tutorial-like.",
  },
] as const;

export const DEFAULT_VERBOSITY = 3;

export function getVerbosityPrompt(level: number): string {
  const entry = VERBOSITY_LEVELS.find((v) => v.level === level);
  return entry?.prompt ?? VERBOSITY_LEVELS[2].prompt;
}

export function VerbositySlider() {
  const { settings, updateSetting } = useSettings();
  const currentLevel =
    (settings.voice?.verbosity as number) || DEFAULT_VERBOSITY;

  const currentEntry =
    VERBOSITY_LEVELS.find((v) => v.level === currentLevel) ??
    VERBOSITY_LEVELS[2];

  return (
    <div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "0.4rem",
        }}
      >
        <label
          htmlFor="verbosity-slider"
          style={{
            fontSize: "0.8rem",
            color: "#94a3b8",
          }}
        >
          Verbosity
        </label>
        <span
          data-testid="verbosity-level-label"
          style={{
            fontSize: "0.75rem",
            color: "#e2e8f0",
            fontWeight: 600,
          }}
        >
          {currentLevel} — {currentEntry.name}
        </span>
      </div>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "0.5rem",
        }}
      >
        <span style={{ fontSize: "0.7rem", color: "#64748b" }}>Concise</span>
        <input
          id="verbosity-slider"
          data-testid="verbosity-slider"
          type="range"
          min={1}
          max={5}
          step={1}
          value={currentLevel}
          onChange={(e) =>
            updateSetting("voice", "verbosity", Number(e.target.value))
          }
          style={{
            flex: 1,
            accentColor: "#6366f1",
            cursor: "pointer",
          }}
        />
        <span style={{ fontSize: "0.7rem", color: "#64748b" }}>Wordy</span>
      </div>
      <div
        style={{
          position: "relative",
          display: "inline-block",
          marginTop: "0.4rem",
        }}
      >
        <span
          data-testid="verbosity-tooltip-trigger"
          title={`Level 1 is extremely concise — may skip supporting details. Level 5 gives full explanations with context and examples. Current: Level ${currentLevel} (${currentEntry.name}).`}
          style={{
            fontSize: "0.7rem",
            color: "#64748b",
            cursor: "help",
            textDecoration: "underline dotted",
          }}
        >
          (?) What does this mean?
        </span>
      </div>
    </div>
  );
}
