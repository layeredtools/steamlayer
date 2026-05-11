import { useState, useEffect } from "react";
import { useAppStore } from "@/store";
import { useSettings } from "@/hooks";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { X, FolderOpen } from "lucide-react";
import { toast } from "sonner";

export default function SettingsPanel() {
  const { settingsOpen, closeSettings } = useAppStore();
  const { settings, saving, error, save } = useSettings();

  const [cacheDir, setCacheDir] = useState("");
  const [ttl, setTtl] = useState("");
  const [fetchDlcs, setFetchDlcs] = useState(true);
  const [strict, setStrict] = useState(false);
  const [allowNetwork, setAllowNetwork] = useState(true);

  const TTL_PRESETS = [
    { label: "15 minutes", seconds: 900 },
    { label: "1 hour", seconds: 3600 },
    { label: "6 hours", seconds: 21600 },
    { label: "1 day", seconds: 86400 },
    { label: "1 week", seconds: 604800 },
  ];

  useEffect(() => {
    if (!settings) return;
    setCacheDir(settings.cache_dir);
    setTtl(String(settings.dlc_cache_ttl_seconds));
    setFetchDlcs(settings.fetch_dlcs);
    setStrict(settings.strict);
    setAllowNetwork(settings.allow_network);
  }, [settings]);

  const pickCacheDir = async () => {
    const path = await window.electron.openFolder();
    if (path) setCacheDir(path);
  };

  const handleSave = async () => {
    const ok = await save({
      cache_dir: cacheDir,
      dlc_cache_ttl_seconds: parseInt(ttl, 10),
      fetch_dlcs: fetchDlcs,
      strict,
      allow_network: allowNetwork,
    });

    if (ok) {
      toast.success("Settings saved");
      closeSettings();
    } else {
      toast.error(error ?? "Failed to save settings.");
    }
  };

  return (
    <>
      {/* Backdrop */}
      <div
        className="absolute inset-0 z-10"
        style={{
          opacity: settingsOpen ? 1 : 0,
          pointerEvents: settingsOpen ? "all" : "none",
          background: "rgba(0,0,0,0.4)",
          backdropFilter: "blur(2px)",
          transition: "opacity 200ms ease",
        }}
        onClick={closeSettings}
      />

      {/* Panel */}
      <div
        className="absolute top-0 right-0 h-full w-80 z-20 flex flex-col bg-black/60 backdrop-blur-md border-l border-zinc-800"
        style={{
          transform: settingsOpen ? "translateX(0)" : "translateX(100%)",
          transition: "transform 250ms cubic-bezier(0.22,1,0.36,1)",
        }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-zinc-800">
          <span className="text-sm font-medium font-mono">Settings</span>
          <button onClick={closeSettings} className="text-zinc-500 hover:text-zinc-300 transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-6 scrollbar-none">

          {/* Network */}
          <Section title="Network">
            <Toggle
              label="Allow network"
              description="Fetch game data from Steam"
              value={allowNetwork}
              onChange={setAllowNetwork}
            />
          </Section>

          <Separator className="bg-zinc-800" />

          {/* Resolution */}
          <Section title="Resolution">
            <Toggle
              label="Strict mode"
              description="Reject low confidence matches"
              value={strict}
              onChange={setStrict}
            />
          </Section>

          <Separator className="bg-zinc-800" />

          {/* Cache */}
          <Section title="Cache">
            <Label className="text-xs text-zinc-400">Cache directory</Label>
            <div className="flex gap-2 mt-1.5">
              <Input
                value={cacheDir}
                onChange={(e) => setCacheDir(e.target.value)}
                className="bg-black/40 border-zinc-700 font-mono text-xs h-8 flex-1 min-w-0"
              />
              <button
                onClick={pickCacheDir}
                className="shrink-0 px-2 h-8 rounded border border-zinc-700 text-zinc-400 hover:text-zinc-200 hover:border-zinc-500 transition-colors"
              >
                <FolderOpen className="w-3.5 h-3.5" />
              </button>
            </div>
          </Section>
          
          <Separator className="bg-zinc-800" />

          {/* DLC */}
          <Section title="DLC">
            <Toggle
              label="Fetch DLCs"
              description="Hydrate DLC metadata on resolve"
              value={fetchDlcs}
              onChange={setFetchDlcs}
            />
            <div className="space-y-1.5 mt-3">
              <Label className="text-xs text-zinc-400">Cache TTL</Label>
              <select
                value={ttl}
                onChange={(e) => setTtl(e.target.value)}
                className="w-full h-8 bg-black/40 border border-zinc-700 rounded-md px-2 text-sm font-mono text-zinc-300 cursor-pointer"
              >
                {TTL_PRESETS.map((p) => (
                  <option key={p.seconds} value={String(p.seconds)}>
                    {p.label}
                  </option>
                ))}
              </select>
            </div>
          </Section>

          {error && (
            <p className="text-xs text-red-400 font-mono">{error}</p>
          )}
        </div>

        {/* Footer */}
        <div className="px-5 py-4 border-t border-zinc-800">
          <Button
            onClick={handleSave}
            disabled={saving || !settings}
            className="w-full bg-white/10 hover:bg-white/15 text-zinc-100 border border-white/10 backdrop-blur-sm font-medium transition-colors"
          >
            {saving ? "Saving..." : "Save changes"}
          </Button>
        </div>
      </div>
    </>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="space-y-2">
      <p className="text-xs text-zinc-600 font-mono uppercase tracking-widest">{title}</p>
      {children}
    </div>
  );
}

function Toggle({
  label,
  description,
  value,
  onChange,
}: {
  label: string;
  description: string;
  value: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between gap-4">
      <div>
        <p className="text-sm text-zinc-300">{label}</p>
        <p className="text-xs text-zinc-600">{description}</p>
      </div>
        <button
          onClick={() => onChange(!value)}
          style={{ transform: "none" }}
          className={`toggle relative w-9 h-5 rounded-full transition-colors shrink-0 ${
            value ? "bg-blue-500/70" : "bg-zinc-700"
          }`}
        >
        <span
          className="absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform"
          style={{ transform: value ? "translateX(16px)" : "translateX(0)" }}
        />
      </button>
    </div>
  );
}