"use client";

import { createContext, useContext, useReducer, useEffect, useCallback, useRef, type ReactNode } from "react";
import type { Room } from "livekit-client";

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

type SettingsAction =
  | { type: "HYDRATE"; state: SettingsState }
  | { type: "UPDATE"; category: string; key: string; value: unknown };

function settingsReducer(state: SettingsState, action: SettingsAction): SettingsState {
  switch (action.type) {
    case "HYDRATE":
      return action.state;
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
  const [settings, dispatch] = useReducer(settingsReducer, DEFAULT_SETTINGS);

  // Hydrate from localStorage after mount to avoid server/client mismatch
  useEffect(() => {
    const stored = loadSettings();
    if (JSON.stringify(stored) !== JSON.stringify(DEFAULT_SETTINGS)) {
      dispatch({ type: "HYDRATE", state: stored });
    }
  }, []);

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

/**
 * Syncs settings changes to the LiveKit agent via data channel.
 *
 * Watches model and verbosity settings; when they change, publishes a
 * settings_update message to the room data channel after a 300ms debounce.
 * Skips the initial render to avoid sending on mount.
 */
export function useSettingsSync(room: Room | null | undefined) {
  const { settings } = useSettings();
  const model = settings.model?.anthropicModel as string | undefined;
  const verbosity = settings.voice?.verbosity as number | undefined;
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const initialRef = useRef(true);

  useEffect(() => {
    // Skip initial render — don't send on mount
    if (initialRef.current) {
      initialRef.current = false;
      return;
    }

    if (!room) return;

    // Debounce: clear previous timeout
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    debounceRef.current = setTimeout(() => {
      const payload = JSON.stringify({
        type: "settings_update",
        ...(model !== undefined && { model }),
        ...(verbosity !== undefined && { verbosity }),
      });

      try {
        room.localParticipant.publishData(
          new TextEncoder().encode(payload),
          { topic: "settings" },
        );
      } catch (err) {
        console.error("Failed to send settings update via data channel:", err);
      }
    }, 300);

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [room, model, verbosity]);
}
