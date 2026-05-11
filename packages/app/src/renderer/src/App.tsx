import { useEffect, useState, useRef, JSX } from "react";
import { useAppStore } from "@/store";
import IdlePage from "@/pages/IdlePage";
import ResolvingPage from "@/pages/ResolvingPage";
import DisambiguationPage from "@/pages/DisambiguationPage";
import ConfirmationPage from "@/pages/ConfirmationPage";
import ResolvedPage from "@/pages/ResolvedPage";
import PatchingPage from "@/pages/PatchingPage";
import ErrorPage from "@/pages/ErrorPage";
import DitherBackground from "@/components/DitherBackground";
import SettingsPanel from "@/components/SettingsPanel";
import { Settings } from "lucide-react";
import { Toaster } from "@/components/ui/sonner";

type Status = "idle" | "resolving" | "pending_disambiguation" | "pending_confirmation" | "resolved" | "patching" | "error";

const DEPTH: Record<Status, number> = {
  idle: 0,
  resolving: 1,
  pending_disambiguation: 2,
  pending_confirmation: 2,
  resolved: 3,
  patching: 4,
  error: 5,
};

const PAGES: Record<Status, JSX.Element> = {
  idle: <IdlePage />,
  resolving: <ResolvingPage />,
  pending_disambiguation: <DisambiguationPage />,
  pending_confirmation: <ConfirmationPage />,
  resolved: <ResolvedPage />,
  patching: <PatchingPage />,
  error: <ErrorPage />,
};

type Phase = "idle" | "exit" | "enter";

export default function App() {
  const status = useAppStore((s) => s.status);
  const settingsOpen = useAppStore((s) => s.settingsOpen);
  const openSettings = useAppStore((s) => s.openSettings);
  const [displayStatus, setDisplayStatus] = useState<Status>(status);
  const [phase, setPhase] = useState<Phase>("idle");
  const [direction, setDirection] = useState<1 | -1>(1);
  const bgRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (status === displayStatus) return;

    const dir = DEPTH[status] >= DEPTH[displayStatus] ? 1 : -1;
    setDirection(dir);
    setPhase("exit");

    const swap = setTimeout(() => {
      setDisplayStatus(status);
      setPhase("enter");
    }, 180);

    const settle = setTimeout(() => {
      setPhase("idle");
    }, 360);

    return () => {
      clearTimeout(swap);
      clearTimeout(settle);
    };
  }, [status]);

  useEffect(() => {
    let targetX = 50;
    let targetY = 30;
    let currentX = 50;
    let currentY = 30;
    let rafId: number;
    let lastGradientUpdate = 0;

    const handleMouseMove = (e: MouseEvent) => {
      targetX = 50 + ((e.clientX / window.innerWidth) * 100 - 50) * 0.18;
      targetY = 30 + ((e.clientY / window.innerHeight) * 100 - 50) * 0.18;
    };

    const animate = (timestamp: number) => {
      currentX += (targetX - currentX) * 0.03;
      currentY += (targetY - currentY) * 0.03;

      if (timestamp - lastGradientUpdate > 50 && bgRef.current) {
        bgRef.current.style.background = `radial-gradient(ellipse at ${currentX}% ${currentY}%, #0d1a2e 0%, #0a0a0f 65%)`;
        lastGradientUpdate = timestamp;
      }

      rafId = requestAnimationFrame(animate);
    };

    window.addEventListener("mousemove", handleMouseMove);
    rafId = requestAnimationFrame(animate);

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      cancelAnimationFrame(rafId);
    };
  }, []);

  const getStyle = (): React.CSSProperties => {
    const SLIDE = 24;

    if (phase === "exit") return {
      opacity: 0,
      transform: `translateY(${-SLIDE * direction}px) scale(0.97)`,
      filter: "blur(4px)",
      transition: "opacity 180ms ease, transform 180ms ease, filter 180ms ease",
    };

    if (phase === "enter") return {
      opacity: 0,
      transform: `translateY(${SLIDE * direction}px) scale(0.97)`,
      filter: "blur(4px)",
      transition: "none",
    };

    return {
      opacity: 1,
      transform: "translateY(0px) scale(1)",
      filter: "blur(0px)",
      transition: "opacity 220ms ease, transform 220ms cubic-bezier(0.22,1,0.36,1), filter 220ms ease",
    };
  };

  return (
    <div
      ref={bgRef}
      className="relative h-screen w-screen flex flex-col overflow-hidden"
      style={{ background: "radial-gradient(ellipse at 50% 30%, #0d1a2e 0%, #0a0a0f 65%)" }}
    >
      <DitherBackground />

      {!settingsOpen && (
        <div className="absolute top-4 right-4 z-30">
          <button
            onClick={openSettings}
            className="text-zinc-600 hover:text-zinc-300 transition-colors"
          >
            <Settings className="w-5 h-5" />
          </button>
        </div>
      )}

      <SettingsPanel />
      <div style={{ ...getStyle(), height: "100%", position: "relative", zIndex: 1 }}>
        {PAGES[displayStatus]}
      </div>

      <Toaster position="bottom-center" theme="dark" />
    </div>
  );
}