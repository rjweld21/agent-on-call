"use client";

import { createContext, useContext, useReducer, useEffect, useCallback, type ReactNode } from "react";

const STORAGE_KEY = "aoc-settings";

export interface SettingsState {
  general: Record<string, unknown>;
  model: Record<string, unknown>;
  voice: Record<string, unknown>;
  [category: string]: Record<string, unknown>;
}

export const DEFAULT_SETTINGS: SettingsState = {
  general: {},
  model: {},
  voice: {},
};

type SettingsAction = {
  type: "UPDATE";
  category: string;
  key: string;
  value: unknown;
};

function settingsReducer(state: SettingsState, action: SettingsAction): SettingsState {
  switch (action.type) {
    case "UPDATE": {
      const updated = {
        ...state,
        [action.category]: {
          ...(state[action.category] ?? {}),
          [action.key]: action.value,
        },
      };
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      } catch {
        // localStorage may be unavailable
      }
      return updated;
    }
    default:
      return state;
  }
}

function loadSettings(): SettingsState {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
        return { ...DEFAULT_SETTINGS, ...parsed };
      }
    }
  } catch {
    // Invalid JSON or localStorage unavailable
  }
  return DEFAULT_SETTINGS;
}

interface SettingsContextValue {
  settings: SettingsState;
  updateSetting: (category: string, key: string, value: unknown) => void;
}

const SettingsContext = createContext<SettingsContextValue | null>(null);

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [settings, dispatch] = useReducer(settingsReducer, DEFAULT_SETTINGS, loadSettings);

  const updateSetting = useCallback(
    (category: string, key: string, value: unknown) => {
      dispatch({ type: "UPDATE", category, key, value });
    },
    [],
  );

  return (
    <SettingsContext.Provider value={{ settings, updateSetting }}>
      {children}
    </SettingsContext.Provider>
  );
}

export function useSettings(): SettingsContextValue {
  const context = useContext(SettingsContext);
  if (!context) {
    throw new Error("useSettings must be used within a SettingsProvider");
  }
  return context;
}
