import { useEffect, useRef } from "react";
import type { ProgressEvent } from "@/api";

interface Props {
  events: ProgressEvent[];
}

export default function ProgressConsole({ events }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events]);

  return (
    <div className="w-full max-w-md bg-black/40 backdrop-blur-sm border border-zinc-800 rounded-lg overflow-hidden">
      <div className="px-4 py-2 border-b border-zinc-800 flex items-center gap-2">
        <div className="w-1.5 h-1.5 rounded-full bg-zinc-500 animate-pulse" />
        <span className="text-xs text-zinc-500 font-mono">progress</span>
      </div>

      <div className="p-4 h-48 overflow-y-auto space-y-1 scrollbar-none">
        {events.length === 0 ? (
          <p className="text-xs text-zinc-600 font-mono">Waiting for events...</p>
        ) : (
          events.map((e, i) => {
            const isLatest = i === events.length - 1;
            return (
              <div
                key={i}
                className="flex gap-3 items-start"
                style={{ opacity: isLatest ? 1 : 0.4 + (i / events.length) * 0.5 }}
              >
                <span className="text-zinc-600 font-mono text-xs shrink-0 pt-px">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <span className="text-xs font-mono text-zinc-300 leading-relaxed">
                  <span className="text-zinc-500">{e.event}</span>
                  {e.detail && (
                    <>
                      <span className="text-zinc-700 mx-1">→</span>
                      <span>{e.detail}</span>
                    </>
                  )}
                </span>
              </div>
            );
          })
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}