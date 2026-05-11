import { useEffect, useState } from "react";
import { getSettings, updateSettings } from "@/api";
import type { Settings, SettingsPatch } from "@/api";

export function useSettings() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getSettings()
      .then(setSettings)
      .catch((e) => setError(e.message));
  }, []);

  const save = async (patch: SettingsPatch): Promise<boolean> => {
    setSaving(true);
    setError(null);
    try {
      const updated = await updateSettings(patch);
      setSettings(updated);
      return true;
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Failed to save settings.";
      setError(msg);
      return false;
    } finally {
      setSaving(false);
    }
  };

  return { settings, saving, error, save };
}