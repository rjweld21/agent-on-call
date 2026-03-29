"use client";

import { useSettings } from "@/lib/settings-context";

export const ANTHROPIC_MODELS = [
  { value: "claude-haiku-4-5-20250514", label: "Claude Haiku 4.5" },
  { value: "claude-sonnet-4-5-20250514", label: "Claude Sonnet 4.5" },
  { value: "claude-opus-4-20250514", label: "Claude Opus 4" },
] as const;

export const DEFAULT_MODEL = "claude-sonnet-4-5-20250514";

export const VALID_MODEL_IDS = ANTHROPIC_MODELS.map((m) => m.value);

export function ModelSelector() {
  const { settings, updateSetting } = useSettings();
  const currentModel =
    (settings.model?.anthropicModel as string) || DEFAULT_MODEL;

  return (
    <div>
      <label
        htmlFor="model-selector"
        style={{
          display: "block",
          fontSize: "0.8rem",
          color: "#94a3b8",
          marginBottom: "0.4rem",
        }}
      >
        Anthropic Model
      </label>
      <select
        id="model-selector"
        data-testid="model-selector"
        value={currentModel}
        onChange={(e) =>
          updateSetting("model", "anthropicModel", e.target.value)
        }
        style={{
          width: "100%",
          padding: "0.5rem 0.75rem",
          background: "#1e293b",
          border: "1px solid #475569",
          borderRadius: "6px",
          color: "#e2e8f0",
          fontSize: "0.85rem",
          cursor: "pointer",
          outline: "none",
        }}
      >
        {ANTHROPIC_MODELS.map((model) => (
          <option key={model.value} value={model.value}>
            {model.label}
          </option>
        ))}
      </select>
    </div>
  );
}
