import { useEffect, useState } from "react";
import { useAppStore } from "@/store";
import { usePatch } from "@/hooks";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { getPatchStatus } from "@/api";
import { Loader2 } from "lucide-react";

export default function ResolvedPage() {
  const { game, gamePath, reset } = useAppStore();
  const { patch, unpatch } = usePatch();
  const [isPatched, setIsPatched] = useState<boolean | null>(null);

  useEffect(() => {
    if (!gamePath) return;
    getPatchStatus(gamePath).then((r) => setIsPatched(r.is_patched));
  }, [gamePath]);

  if (!game) return null;

  const dlcCount = Object.keys(game.dlcs).length;

  return (
    <div className="flex flex-col items-center justify-center h-full gap-6 px-8">
      <div className="w-full max-w-md border border-zinc-800 rounded-lg overflow-hidden bg-black/40 backdrop-blur-sm shadow-[0_0_30px_rgba(0,0,0,0.5)]">
        <div className="w-full h-32 overflow-hidden relative">
          <img
            src={`https://cdn.akamai.steamstatic.com/steam/apps/${game.appid}/header.jpg`}
            alt={game.game_name ?? "Game"}
            className="w-full h-full object-cover"
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = "none";
            }}
          />
          <div className="absolute inset-0 bg-gradient-to-b from-transparent to-black/60" />
        </div>

        <div className="px-5 py-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="font-semibold text-base">
                {game.game_name ?? `App ${game.appid}`}
              </h2>
              <p className="text-xs text-zinc-500 font-mono mt-0.5">{game.appid}</p>
            </div>
            <div className="flex gap-2 shrink-0">
              {isPatched && (
                <Badge className="bg-blue-500/20 text-blue-300 border-blue-500/30">
                  patched
                </Badge>
              )}
              <Badge variant="outline" className="text-zinc-400 border-zinc-700">
                {game.source}
              </Badge>
            </div>
          </div>
        </div>

        <Separator className="bg-zinc-800" />

        <div className="px-5 py-3 flex items-center justify-between">
          <span className="text-sm text-zinc-400">DLCs found</span>
          <span className="text-sm font-mono">{dlcCount}</span>
        </div>

        <Separator className="bg-zinc-800" />

        <div className="px-5 py-3">
          <p className="text-xs text-zinc-600 font-mono truncate">{gamePath}</p>
        </div>
      </div>

      <div className="flex gap-3 w-full max-w-md">
        <Button
          variant="outline"
          className="flex-1 bg-transparent hover:bg-white/5 text-zinc-400 border border-zinc-800 font-medium transition-colors"
          onClick={reset}
        >
          Back
        </Button>

        {isPatched === null ? (
          <Button disabled className="flex-1 bg-white/5 border border-zinc-800 text-zinc-600 font-medium">
            <Loader2 className="w-3.5 h-3.5 animate-spin mr-2" />
            Checking...
          </Button>
        ) : isPatched ? (
          <Button
            className="flex-1 bg-red-500/20 hover:bg-red-500/30 text-red-300 border border-red-500/30 backdrop-blur-sm font-medium transition-colors"
            onClick={unpatch}
          >
            Unpatch game
          </Button>
        ) : (
          <Button
            className="flex-1 bg-white/10 hover:bg-white/15 text-zinc-100 border border-white/10 backdrop-blur-sm font-medium transition-colors"
            onClick={patch}
          >
            Patch game
          </Button>
        )}
      </div>
    </div>
  );
}