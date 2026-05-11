import { useAppStore } from "@/store";
import { Button } from "@/components/ui/button";
import { AlertCircle } from "lucide-react";

export default function ErrorPage() {
  const { error, reset } = useAppStore();

  return (
    <div className="flex flex-col items-center justify-center h-full gap-4 px-8">
      <AlertCircle className="w-10 h-10 text-red-500/70" />
      <div className="text-center">
        <h2 className="text-lg font-semibold">Something went wrong</h2>
        <p className="text-sm text-zinc-500 mt-1 font-mono max-w-sm break-words">
          {error}
        </p>
      </div>
      <Button variant="outline" className="border-zinc-700 mt-2" onClick={reset}>
        Try again
      </Button>
    </div>
  );
}