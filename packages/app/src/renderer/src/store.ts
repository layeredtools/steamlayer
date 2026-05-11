// renderer/src/store.ts

import { create } from "zustand";
import type { ResolvedGame, PendingEvent, ProgressEvent } from "@/api";

type Status =
  | "idle"
  | "resolving"
  | "pending_disambiguation"
  | "pending_confirmation"
  | "resolved"
  | "patching"
  | "error";

interface AppState {
  status: Status;
  gamePath: string | null;
  game: ResolvedGame | null;
  pendingEvent: PendingEvent | null;
  progress: ProgressEvent[];
  error: string | null;
  settingsOpen: boolean;

  openSettings: () => void;
  closeSettings: () => void;
  setGamePath: (path: string) => void;
  setResolving: () => void;
  setPending: (event: PendingEvent) => void;
  setResolved: (game: ResolvedGame) => void;
  setPatching: () => void;
  setError: (message: string) => void;
  pushProgress: (event: ProgressEvent) => void;
  reset: () => void;
}

const initialState = {
  settingsOpen: false,
  status: "idle" as Status,
  gamePath: null,
  game: null,
  pendingEvent: null,
  progress: [],
  error: null,
};

export const useAppStore = create<AppState>((set) => ({
  ...initialState,

  setGamePath: (path) => set({ gamePath: path }),

  openSettings: () => set({ settingsOpen: true }),
  closeSettings: () => set({ settingsOpen: false }),

  setResolving: () =>
    set({ status: "resolving", progress: [], error: null, game: null }),

  setPending: (event) =>
    set({
      status:
        event.type === "AmbiguousMatchEvent"
          ? "pending_disambiguation"
          : "pending_confirmation",
      pendingEvent: event,
    }),

  setResolved: (game) =>
    set({ status: "resolved", game, pendingEvent: null }),

  setPatching: () =>
    set({ status: "patching", progress: [] }),

  setError: (message) =>
    set({ status: "error", error: message }),

  pushProgress: (event) =>
    set((s) => ({ progress: [...s.progress, event] })),

  reset: () => set(initialState),
}));