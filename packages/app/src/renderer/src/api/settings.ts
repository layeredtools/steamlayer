import { request } from "./client";
import type { Settings, SettingsPatch } from "./types";

export const getSettings = () =>
  request<Settings>("GET", "/settings");

export const updateSettings = (patch: SettingsPatch) =>
  request<Settings>("PATCH", "/settings", patch);