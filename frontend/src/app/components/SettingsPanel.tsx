"use client";

import { useEffect, useCallback } from "react";
import { ModelSelector } from "./ModelSelector";
import { VerbositySlider } from "./VerbositySlider";

interface SettingsPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

const SECTIONS = [
  { id: "general", title: "General", description: "General preferences" },
  { id: "model", title: "Model", description: "AI model configuration", component: ModelSelector },
  { id: "voice", title: "Voice", description: "Voice and turn-taking controls", component: VerbositySlider },
];

export function SettingsPanel({ isOpen, onClose }: SettingsPanelProps) {
  const handleKeyDown = useCallback(
    (e: globalThis.KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    },
    [isOpen, onClose],
  );

  useEffect(() => {
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        data-testid="settings-backdrop"
        onClick={onClose}
        style={{
          position: "fixed",
          inset: 0,
          background: "rgba(0, 0, 0, 0.5)",
          zIndex: 40,
        }}
      />

      {/* Panel */}
      <div
        role="dialog"
        aria-label="Settings panel"
        style={{
          position: "fixed",
          top: 0,
          right: 0,
          bottom: 0,
          width: "360px",
          maxWidth: "90vw",
          background: "#1e293b",
          borderLeft: "1px solid #334155",
          zIndex: 50,
          display: "flex",
          flexDirection: "column",
          fontFamily: "system-ui, sans-serif",
          color: "#e2e8f0",
          animation: "slideIn 0.2s ease-out",
        }}
      >
        {/* Header */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "1rem 1.25rem",
            borderBottom: "1px solid #334155",
          }}
        >
          <h2 style={{ margin: 0, fontSize: "1.2rem", fontWeight: "bold" }}>
            Settings
          </h2>
          <button
            onClick={onClose}
            aria-label="Close settings"
            style={{
              background: "none",
              border: "none",
              color: "#94a3b8",
              cursor: "pointer",
              fontSize: "1.4rem",
              lineHeight: 1,
              padding: "0.25rem",
            }}
          >
            &times;
          </button>
        </div>

        {/* Sections */}
        <div
          style={{
            flex: 1,
            overflowY: "auto",
            padding: "1rem 1.25rem",
          }}
        >
          {SECTIONS.map((section) => {
            const SectionComponent = section.component;
            return (
              <div
                key={section.id}
                style={{
                  marginBottom: "1.5rem",
                }}
              >
                <h3
                  style={{
                    fontSize: "0.95rem",
                    fontWeight: 600,
                    color: "#e2e8f0",
                    margin: "0 0 0.25rem 0",
                  }}
                >
                  {section.title}
                </h3>
                <p
                  style={{
                    fontSize: "0.75rem",
                    color: "#64748b",
                    margin: "0 0 0.75rem 0",
                  }}
                >
                  {section.description}
                </p>
                <div
                  style={{
                    padding: "0.75rem",
                    background: "#0f172a",
                    borderRadius: "6px",
                    border: "1px solid #334155",
                  }}
                >
                  {SectionComponent ? (
                    <SectionComponent />
                  ) : (
                    <p
                      style={{
                        margin: 0,
                        color: "#475569",
                        fontSize: "0.8rem",
                        fontStyle: "italic",
                      }}
                    >
                      No settings available yet.
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </>
  );
}
