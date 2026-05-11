import { request } from "./client";
import type { ResolvedGame, PatchResult, UnpatchResponse, PatchStatus } from "./types";

export const patchGame = (game: ResolvedGame, path: string) =>
  request<PatchResult>("POST", "/patch", { game, path });

export const unpatchGame = (path: string) =>
  request<UnpatchResponse>("DELETE", "/patch", { path });

export const getPatchStatus = (path: string) =>
  request<PatchStatus>("GET", `/patch/status?path=${encodeURIComponent(path)}`);