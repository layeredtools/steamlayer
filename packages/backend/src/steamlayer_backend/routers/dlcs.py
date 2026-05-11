from __future__ import annotations

from backend.models import DLCInfoModel, DLCListResponse
from backend.state import state
from fastapi import APIRouter
from steamlayer_core.api import SteamLayerClient

router = APIRouter()


@router.get("/dlcs/{appid}", response_model=DLCListResponse)
async def get_dlcs(appid: int) -> DLCListResponse:
    with SteamLayerClient(
        options=state.options,
        allow_network=state.allow_network,
        progress=state.make_progress_callback(),
    ) as client:
        dlcs = client.fetch_dlcs(appid)

    return DLCListResponse(
        dlcs={k: DLCInfoModel(appid=v.appid, name=v.name, from_cache=v.from_cache) for k, v in dlcs.items()}
    )
