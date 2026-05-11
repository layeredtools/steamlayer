// app/src/main/ipc.ts

import { ipcMain, dialog } from "electron";
import { BACKEND_URL } from "./backend";

export function registerIpcHandlers(): void {
  ipcMain.handle("backend:url", () => BACKEND_URL);

  ipcMain.handle("dialog:openFolder", async () => {
    const result = await dialog.showOpenDialog({
      properties: ["openDirectory"],
    });
    return result.canceled ? null : result.filePaths[0];
  });
}