from __future__ import annotations

from fastapi import APIRouter, HTTPException
from steamlayer_backend.models import (
    PatchRequest,
    PatchResultModel,
    PatchStatusResponse,
    UnpatchRequest,
    UnpatchResponse,
)
from steamlayer_backend.state import state
from steamlayer_backend.vendor import config_writer, vendor
from steamlayer_core.api import SteamLayerClient
from steamlayer_core.domain.exceptions import PatchError, VaultError
from steamlayer_core.domain.models import DLCInfo, ResolutionSource, ResolvedGame

router = APIRouter()


def _to_core_game(body: PatchRequest) -> ResolvedGame:
    return ResolvedGame(
        appid=body.game.appid,
        game_name=body.game.game_name,
        source=ResolutionSource[body.game.source],
        confidence=body.game.confidence,
        dlcs={k: DLCInfo(appid=v.appid, name=v.name, from_cache=v.from_cache) for k, v in body.game.dlcs.items()},
    )


@router.post("/patch", response_model=PatchResultModel)
async def patch(body: PatchRequest) -> PatchResultModel:
    if state.job_running:
        raise HTTPException(status_code=409, detail="A job is already running.")

    state.job_running = True
    try:
        game = _to_core_game(body)
        with SteamLayerClient(
            vendor=vendor,
            config_writer=config_writer,
            progress=state.make_progress_callback(),
        ) as client:
            result = client.patch(game, body.path)

        return PatchResultModel(
            vault_path=str(result.vault_path),
            patched_files=[str(f) for f in result.targets_patched],
        )

    except (PatchError, VaultError) as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        state.job_running = False


@router.delete("/patch", response_model=UnpatchResponse)
async def unpatch(body: UnpatchRequest) -> UnpatchResponse:
    if state.job_running:
        raise HTTPException(status_code=409, detail="A job is already running.")

    state.job_running = True
    try:
        with SteamLayerClient(progress=state.make_progress_callback()) as client:
            restored = client.unpatch(body.path)

        return UnpatchResponse(restored_files=[str(f) for f in restored])

    except (PatchError, VaultError) as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        state.job_running = False


@router.get("/patch/status", response_model=PatchStatusResponse)
async def patch_status(path: str) -> PatchStatusResponse:
    with SteamLayerClient(vendor=vendor, config_writer=config_writer) as client:
        return PatchStatusResponse(is_patched=client.is_patched(path))
