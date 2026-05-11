import { useCallback } from "react";
import { useAppStore } from "@/store";
import { patchGame, unpatchGame, connectProgressSocket } from "@/api";
import type { ProgressEvent } from "@/api";
import { toast } from "sonner";

export function usePatch() {
  const { game, gamePath, setPatching, setPatched, setError, pushProgress, setResolved } =
    useAppStore();

  const patch = useCallback(async () => {
    if (!game || !gamePath) return;

    setPatching();

    const baseUrl = await window.electron.backendUrl();
    const disconnect = connectProgressSocket(
      baseUrl,
      (event: ProgressEvent) => pushProgress(event),
      () => setError("Lost connection to backend.")
    );

    try {
      await patchGame(game, gamePath);
      toast.success(`${game.game_name ?? "Game"} patched successfully`);
      setResolved(game);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Patch failed.");
    } finally {
      disconnect();
    }
  }, [game, gamePath]);

  const unpatch = useCallback(async () => {
    if (!gamePath || !game) return;

    setPatching();

    try {
      await unpatchGame(gamePath);
      toast.success(`${game.game_name ?? "Game"} restored successfully`);
      setResolved(game);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unpatch failed.");
    }
  }, [game, gamePath]);

  return { patch, unpatch };
}