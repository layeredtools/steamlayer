// renderer/src/pages/IdlePage.tsx
import { useAppStore } from "@/store";
import { useResolve } from "@/hooks";
import { Button } from "@/components/ui/button";
import { FolderOpen } from "lucide-react";

export default function IdlePage() {
  const { gamePath, setGamePath } = useAppStore();
  const { resolve } = useResolve();

  const pickFolder = async () => {
    const path = await window.electron.openFolder();
    if (path) setGamePath(path);
  };

  return (
    <div className="flex flex-col items-center justify-center h-full gap-6 px-8">
      <div className="text-center">
        <h1 className="text-2xl font-semibold tracking-tight">SteamLayer</h1>
        <p className="text-sm text-zinc-500 mt-1">Select a game folder to get started</p>
      </div>

      <div
        onClick={pickFolder}
        className="hover-lift w-full max-w-md border border-dashed border-zinc-700 rounded-lg p-8 flex flex-col items-center gap-3 cursor-pointer hover:border-zinc-500 hover:bg-black/40 backdrop-blur-sm transition-colors bg-black/30"
      >
        <FolderOpen className="w-8 h-8 text-zinc-500" />
        <span className="text-sm text-zinc-400">
          {gamePath ?? "Click to browse"}
        </span>
        {gamePath && (
          <span className="text-xs text-zinc-600 font-mono break-all text-center">
            {gamePath}
          </span>
        )}
      </div>

      <Button
        disabled={!gamePath}
        onClick={resolve}
        className="w-full max-w-md bg-white/10 hover:bg-white/15 text-zinc-100 border border-white/10 backdrop-blur-sm font-medium transition-colors"
      >
        Resolve game
      </Button>
    </div>
  );
}