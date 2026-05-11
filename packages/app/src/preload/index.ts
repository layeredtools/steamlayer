// app/src/preload/index.ts

import { contextBridge, ipcRenderer } from "electron";

export type ElectronAPI = typeof api;

const api = {
  backendUrl: (): Promise<string> =>
    ipcRenderer.invoke("backend:url"),

  openFolder: (): Promise<string | null> =>
    ipcRenderer.invoke("dialog:openFolder"),
};

contextBridge.exposeInMainWorld("electron", api);

// Augment Window so renderer TypeScript knows about window.electron
declare global {
  interface Window {
    electron: ElectronAPI;
  }
}