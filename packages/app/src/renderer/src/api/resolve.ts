import { request } from "./client";
import type {
  ResolvedGame,
  PendingEventResponse,
  CandidateModel,
} from "./types";

export const resolveGame = (path: string) =>
  request<ResolvedGame>("POST", "/resolve", { path });

export const getPending = () =>
  request<PendingEventResponse>("GET", "/resolve/pending");

export const disambiguate = (appid: number) =>
  request<{ ok: boolean }>("POST", "/resolve/disambiguate", { appid });

export const confirm = (
  accept: boolean,
  manual_appid?: number
) => request<{ ok: boolean }>("POST", "/resolve/confirm", { accept, manual_appid });