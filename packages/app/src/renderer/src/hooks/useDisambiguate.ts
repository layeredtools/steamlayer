import { useCallback } from "react";
import { useAppStore } from "@/store";
import { disambiguate, confirm } from "@/api";

export function useDisambiguate() {
  const { setError } = useAppStore();

  const pickCandidate = useCallback(async (appid: number) => {
    try {
      await disambiguate(appid);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Disambiguation failed.");
    }
  }, []);

  const acceptCandidate = useCallback(async () => {
    try {
      await confirm(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Confirmation failed.");
    }
  }, []);

  const rejectCandidate = useCallback(async (manualAppid?: number) => {
    try {
      await confirm(false, manualAppid);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Confirmation failed.");
    }
  }, []);

  return { pickCandidate, acceptCandidate, rejectCandidate };
}