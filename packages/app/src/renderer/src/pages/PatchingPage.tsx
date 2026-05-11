// PatchingPage.tsx
import { useAppStore } from "@/store";
import { Loader2 } from "lucide-react";
import ProgressConsole from "@/components/ProgressConsole";

export default function PatchingPage() {
  const { game, progress } = useAppStore();

  return (
    <div className="flex flex-col items-center justify-center h-full gap-4 px-8">
      <div className="flex flex-col items-center gap-2">
        <Loader2 className="w-6 h-6 text-zinc-400 animate-spin" />
        <p className="text-sm text-zinc-300 font-medium">
          Patching {game?.game_name ?? "game"}...
        </p>
      </div>
      <ProgressConsole events={progress} />
    </div>
  );
}