import { useEffect, useState } from "react";
import { useAppStore } from "@/store";
import { AlertCircle } from "lucide-react";
import ProgressConsole from "@/components/ProgressConsole";

export default function ResolvingPage() {
  const progress = useAppStore((s) => s.progress);
  const [wsDropped, setWsDropped] = useState(false);

  useEffect(() => {
    const handler = (e: CustomEvent) => {
      if (e.detail === "ws_dropped") setWsDropped(true);
    };
    window.addEventListener("steamlayer:event" as any, handler);
    return () => window.removeEventListener("steamlayer:event" as any, handler);
  }, []);

  return (
    <div className="flex flex-col items-center justify-center h-full gap-4 px-8">
      {wsDropped ? (
        <AlertCircle className="w-6 h-6 text-yellow-500/70" />
      ) : (
        <div className="w-2 h-2 rounded-full bg-zinc-400 animate-pulse" />
      )}
      <p className="text-sm text-zinc-400">
        {wsDropped ? "Lost connection — still waiting for result..." : "Resolving game..."}
      </p>
      {wsDropped && (
        <p className="text-xs text-zinc-600 max-w-xs text-center">
          The progress stream dropped but the job is still running. The result will appear when it completes.
        </p>
      )}
      <ProgressConsole events={progress} />
    </div>
  );
}