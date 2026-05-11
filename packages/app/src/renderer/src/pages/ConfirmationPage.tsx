import { useState } from "react";
import { useAppStore } from "@/store";
import { useDisambiguate } from "@/hooks";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { LowConfidenceEventPayload } from "@/api";

export default function ConfirmationPage() {
  const pendingEvent = useAppStore((s) => s.pendingEvent) as LowConfidenceEventPayload;
  const { acceptCandidate, rejectCandidate } = useDisambiguate();
  const [showManual, setShowManual] = useState(false);
  const [manualId, setManualId] = useState("");

  const isValidAppId = (val: string) =>
    /^\d{1,10}$/.test(val.trim()) && parseInt(val, 10) > 0;

  if (!pendingEvent) return null;

  const handleReject = () => {
    if (showManual && manualId) {
      rejectCandidate(parseInt(manualId, 10));
    } else {
      setShowManual(true);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center h-full gap-6 px-8">
      <div className="text-center">
        <h2 className="text-lg font-semibold">Low confidence match</h2>
        <p className="text-sm text-zinc-500 mt-1">
          Is <span className="text-zinc-300">{pendingEvent.game_folder_name}</span> this game?
        </p>
      </div>

      <div className="w-full max-w-md border border-zinc-800 rounded-lg px-4 py-3 flex items-center justify-between bg-black/40 backdrop-blur-sm">
        <span className="text-sm">{pendingEvent.candidate.game_name ?? `App ${pendingEvent.candidate.appid}`}</span>
        <span className="text-xs text-zinc-500 font-mono">
          {Math.round(pendingEvent.candidate.confidence * 100)}% match
        </span>
      </div>

      {showManual && (
        <div className="w-full max-w-md space-y-2">
          <Input
            type="number"
            placeholder="Enter App ID manually"
            value={manualId}
            onChange={(e) => setManualId(e.target.value)}
            className={`w-full bg-black/40 border font-mono ${
              manualId && !isValidAppId(manualId)
                ? "border-red-500/50 focus-visible:ring-red-500/30"
                : "border-zinc-700"
            }`}
          />
          {manualId && !isValidAppId(manualId) && (
            <p className="text-xs text-red-400 font-mono">App IDs are positive numbers only</p>
          )}
        </div>
      )}

      <div className="flex gap-3 w-full max-w-md">
        <Button
          variant="outline"
          className="flex-1 bg-transparent hover:bg-white/5 text-zinc-400 border border-zinc-800 font-medium transition-colors"
          onClick={handleReject}
          disabled={showManual && manualId.length > 0 && !isValidAppId(manualId)}
        >
          {showManual && manualId ? "Use this ID" : "No"}
        </Button>
        <Button
          className="flex-1 bg-white/10 hover:bg-white/15 text-zinc-100 border border-white/10 backdrop-blur-sm font-medium transition-colors"
          onClick={acceptCandidate}
        >
          Yes, that's it
        </Button>
      </div>
    </div>
  );
}