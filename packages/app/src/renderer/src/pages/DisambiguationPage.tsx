import { useState } from "react";
import { useAppStore } from "@/store";
import { useDisambiguate } from "@/hooks";
import { Loader2 } from "lucide-react";
import type { AmbiguousEventPayload } from "@/api";

export default function DisambiguationPage() {
  const pendingEvent = useAppStore((s) => s.pendingEvent) as AmbiguousEventPayload;
  const progress = useAppStore((s) => s.progress);
  const { pickCandidate } = useDisambiguate();
  const [waiting, setWaiting] = useState(false);

  if (!pendingEvent && !waiting) return null;

  const handlePick = async (appid: number) => {
    setWaiting(true);
    await pickCandidate(appid);
  };

  if (waiting) return (
    <div className="flex flex-col items-center justify-center h-full gap-4 px-8">
      <Loader2 className="w-6 h-6 text-zinc-400 animate-spin" />
      <p className="text-sm text-zinc-300 font-medium">Fetching game data...</p>
      <div className="w-full max-w-md bg-black/40 backdrop-blur-sm border border-zinc-800 rounded-lg overflow-hidden">
        <div className="px-4 py-2 border-b border-zinc-800 flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-zinc-500 animate-pulse" />
          <span className="text-xs text-zinc-500 font-mono">progress</span>
        </div>
        <div className="p-4 h-32 overflow-y-auto space-y-1 scrollbar-none">
          {progress.length === 0 ? (
            <p className="text-xs text-zinc-600 font-mono">Waiting for events...</p>
          ) : (
            progress.map((e, i) => {
              const isLatest = i === progress.length - 1;
              return (
                <div key={i} className="flex gap-3 items-start" style={{ opacity: isLatest ? 1 : 0.4 + (i / progress.length) * 0.5 }}>
                  <span className="text-zinc-600 font-mono text-xs shrink-0 pt-px">{String(i + 1).padStart(2, "0")}</span>
                  <span className="text-xs font-mono text-zinc-300 leading-relaxed">
                    <span className="text-zinc-500">{e.event}</span>
                    {e.detail && <><span className="text-zinc-700 mx-1">→</span><span>{e.detail}</span></>}
                  </span>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );

  return (
    <div className="flex flex-col items-center h-full gap-4 px-8 py-8 overflow-hidden">
      <div className="text-center shrink-0">
        <h2 className="text-lg font-semibold">Multiple matches found</h2>
        <p className="text-sm text-zinc-500 mt-1">
          Which game is <span className="text-zinc-300">{pendingEvent.game_folder_name}</span>?
        </p>
      </div>

      <div className="w-full overflow-y-auto scrollbar-none flex-1">
        <div className="grid grid-cols-2 gap-3 pb-2">
          {pendingEvent.candidates.map((c) => (
            <button
              key={c.appid}
              onClick={() => handlePick(c.appid)}
              className="rounded-lg border border-zinc-800 hover:border-zinc-600 transition-all text-left bg-black/40 backdrop-blur-sm overflow-hidden group"
            >
              <div className="w-full h-24 overflow-hidden">
                <img
                  src={`https://cdn.akamai.steamstatic.com/steam/apps/${c.appid}/header.jpg`}
                  alt={c.game_name ?? ""}
                  className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                  onError={(e) => {
                    (e.target as HTMLImageElement).parentElement!.style.display = "none";
                  }}
                />
              </div>
              <div className="flex flex-col px-3 py-2">
                <span className="text-sm text-zinc-200 truncate">{c.game_name ?? `App ${c.appid}`}</span>
                <span className="text-xs text-zinc-500 font-mono">{c.appid}</span>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}