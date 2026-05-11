import type { ProgressEvent } from "./types";

type ProgressHandler = (event: ProgressEvent) => void;
type ErrorHandler = (err: Event) => void;

export function connectProgressSocket(
  baseUrl: string,
  onMessage: ProgressHandler,
  onError?: ErrorHandler
): () => void {
  // HTTP → WS, HTTPS → WSS
  const wsUrl = baseUrl.replace(/^http/, "ws") + "/ws/progress";
  const socket = new WebSocket(wsUrl);

  socket.onmessage = (e) => {
    try {
      onMessage(JSON.parse(e.data) as ProgressEvent);
    } catch {
      // malformed frame — ignore
    }
  };

  if (onError) socket.onerror = onError;

  return () => socket.close();
}