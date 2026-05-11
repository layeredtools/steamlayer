from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class CandidateModel(BaseModel):
    appid: int
    game_name: str | None
    confidence: float
    source: str | None


class DLCInfoModel(BaseModel):
    appid: int
    name: str
    from_cache: bool


class ResolvedGameModel(BaseModel):
    appid: int
    game_name: str | None
    source: str
    confidence: float
    dlcs: dict[int, DLCInfoModel] = {}


class PatchResultModel(BaseModel):
    vault_path: str
    patched_files: list[str]


class SettingsModel(BaseModel):
    cache_dir: str
    dlc_cache_ttl_seconds: int
    fetch_dlcs: bool
    strict: bool
    allow_network: bool


class ResolveRequest(BaseModel):
    path: str


class PatchRequest(BaseModel):
    game: ResolvedGameModel
    path: str


class UnpatchRequest(BaseModel):
    path: str


class SettingsPatchRequest(BaseModel):
    cache_dir: str | None = None
    dlc_cache_ttl_seconds: int | None = None
    fetch_dlcs: bool | None = None
    strict: bool | None = None
    allow_network: bool | None = None


class DisambiguateRequest(BaseModel):
    appid: int  # the appid of the candidate the user chose


class ConfirmRequest(BaseModel):
    accept: bool
    manual_appid: int | None = None  # if the user rejects and supplies their own


class UnpatchResponse(BaseModel):
    restored_files: list[str]


class PatchStatusResponse(BaseModel):
    is_patched: bool


class DLCListResponse(BaseModel):
    dlcs: dict[int, DLCInfoModel]


class ErrorResponse(BaseModel):
    detail: str


class AmbiguousEventPayload(BaseModel):
    type: Literal["AmbiguousMatchEvent"]
    candidates: list[CandidateModel]
    game_folder_name: str


class LowConfidenceEventPayload(BaseModel):
    type: Literal["LowConfidenceEvent"]
    candidate: CandidateModel
    threshold: float
    game_folder_name: str


class PendingEventResponse(BaseModel):
    # None when no decision is currently pending.
    event: AmbiguousEventPayload | LowConfidenceEventPayload | None


class ProgressEvent(BaseModel):
    event: str
    detail: str
