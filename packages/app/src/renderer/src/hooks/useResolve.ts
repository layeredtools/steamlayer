import { useCallback, useEffect, useRef } from "react";
import { useAppStore } from "@/store";
import {
  resolveGame,
  getPending,
  connectProgressSocket,
} from "@/api";
import type { ProgressEvent } from "@/api";

const PENDING_POLL_INTERVAL_MS = 500;

export function useResolve() {
  const { gamePath, setResolving, setPending, setResolved, setError, pushProgress } =
    useAppStore();
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  };

  const resolve = useCallback(async () => {
    if (!gamePath) return;

    setResolving();

    const baseUrl = await window.electron.backendUrl();

    const disconnect = connectProgressSocket(
      baseUrl,
      (event: ProgressEvent) => {
        if (event.event === "pending_decision") {
          stopPolling();
          pollRef.current = setInterval(async () => {
            try {
              const { event: pending } = await getPending();
              if (pending) {
                stopPolling();
                setPending(pending);
              }
            } catch {
              // retry next tick
            }
          }, PENDING_POLL_INTERVAL_MS);
        } else {
          pushProgress(event);
        }
      },
      () => {
      window.dispatchEvent(
        new CustomEvent("steamlayer:event", { detail: "ws_dropped" })
      );
  }
    );

    try {
      const game = await resolveGame(gamePath);
      console.log("resolved game:", game);
      stopPolling();
      setResolved(game);
    } catch (err) {
      stopPolling();
      setError(err instanceof Error ? err.message : "Resolution failed.");
    } finally {
      disconnect();
    }
  }, [gamePath]);

  useEffect(() => () => stopPolling(), []);

  return { resolve };
}

