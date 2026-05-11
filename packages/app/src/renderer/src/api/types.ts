export interface DLCInfo {
  appid: number;
  name: string;
  from_cache: boolean;
}

export interface ResolvedGame {
  appid: number;
  game_name: string | null;
  source: string;
  confidence: number;
  dlcs: Record<number, DLCInfo>;
}

export interface CandidateModel {
  appid: number;
  game_name: string | null;
  confidence: number;
  source: string | null;
}

export interface AmbiguousEventPayload {
  type: "AmbiguousMatchEvent";
  candidates: CandidateModel[];
  game_folder_name: string;
}

export interface LowConfidenceEventPayload {
  type: "LowConfidenceEvent";
  candidate: CandidateModel;
  threshold: number;
  game_folder_name: string;
}

export type PendingEvent = AmbiguousEventPayload | LowConfidenceEventPayload;

export interface PendingEventResponse {
  event: PendingEvent | null;
}

export interface PatchResult {
  vault_path: string;
  patched_files: string[];
}

export interface UnpatchResponse {
  restored_files: string[];
}

export interface PatchStatus {
  is_patched: boolean;
}

export interface DLCListResponse {
  dlcs: Record<number, DLCInfo>;
}

export interface Settings {
  cache_dir: string;
  dlc_cache_ttl_seconds: number;
  fetch_dlcs: boolean;
  strict: boolean;
  allow_network: boolean;
}

export interface SettingsPatch {
  cache_dir?: string;
  dlc_cache_ttl_seconds?: number;
  fetch_dlcs?: boolean;
  strict?: boolean;
  allow_network?: boolean;
}

export interface ProgressEvent {
  event: string;
  detail: string;
}