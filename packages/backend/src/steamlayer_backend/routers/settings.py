from __future__ import annotations

from fastapi import APIRouter
from steamlayer_backend.models import SettingsModel, SettingsPatchRequest
from steamlayer_backend.state import state
from steamlayer_core.domain.models import SteamlayerOptions

router = APIRouter()


def _to_model(options: SteamlayerOptions) -> SettingsModel:
    return SettingsModel(
        cache_dir=str(options.cache_dir),
        dlc_cache_ttl_seconds=options.dlc_cache_ttl_seconds,
        fetch_dlcs=options.fetch_dlcs,
        strict=options.strict,
        allow_network=state.allow_network,
    )


@router.patch("/settings", response_model=SettingsModel)
async def patch_settings(body: SettingsPatchRequest) -> SettingsModel:
    current = state.options

    if body.allow_network is not None:
        state.allow_network = body.allow_network

    state.options = SteamlayerOptions(
        cache_dir=body.cache_dir or current.cache_dir,
        dlc_cache_ttl_seconds=(
            body.dlc_cache_ttl_seconds if body.dlc_cache_ttl_seconds is not None else current.dlc_cache_ttl_seconds
        ),
        fetch_dlcs=body.fetch_dlcs if body.fetch_dlcs is not None else current.fetch_dlcs,
        strict=body.strict if body.strict is not None else current.strict,
    )

    return _to_model(state.options)


@router.get("/settings", response_model=SettingsModel)
async def get_settings() -> SettingsModel:
    return _to_model(state.options)
