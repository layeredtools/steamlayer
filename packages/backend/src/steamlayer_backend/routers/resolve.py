from __future__ import annotations

import asyncio
from functools import partial

from fastapi import APIRouter, HTTPException
from steamlayer_backend.models import (
    AmbiguousEventPayload,
    CandidateModel,
    ConfirmRequest,
    DisambiguateRequest,
    DLCInfoModel,
    LowConfidenceEventPayload,
    PendingEventResponse,
    ResolvedGameModel,
    ResolveRequest,
)
from steamlayer_backend.state import state
from steamlayer_core import SteamLayerClient
from steamlayer_core.domain.exceptions import AppIDResolutionError
from steamlayer_core.domain.models import DiscoveryResult, ResolutionSource
from steamlayer_core.events import AmbiguousMatchEvent, LowConfidenceEvent

router = APIRouter()


def _disambiguation_handler(event: AmbiguousMatchEvent) -> DiscoveryResult:
    """
    Suspends the resolution thread and pushes an AmbiguousMatchEvent to the
    frontend via the progress queue. Resumes once the frontend POSTs to
    /resolve/disambiguate with the chosen candidate's appid.
    """
    state.set_pending(event)
    return state.wait_for_decision()


def _confirmation_handler(event: LowConfidenceEvent) -> DiscoveryResult:
    """
    Suspends the resolution thread and pushes a LowConfidenceEvent to the
    frontend via the progress queue. Resumes once the frontend POSTs to
    /resolve/confirm with accept=True/False and an optional manual appid.
    """
    state.set_pending(event)
    return state.wait_for_decision()


def _do_resolve(path: str) -> ResolvedGameModel:
    """Runs synchronously inside a thread executor."""
    with SteamLayerClient(
        options=state.options,
        allow_network=state.allow_network,
        on_disambiguation=_disambiguation_handler,
        on_confirmation=_confirmation_handler,
        progress=state.make_progress_callback(),
    ) as client:
        game = client.resolve(path)

    return ResolvedGameModel(
        appid=game.appid,
        game_name=game.game_name,
        source=game.source.name if game.source else "MANUAL",
        confidence=game.confidence,
        dlcs={
            k: DLCInfoModel(appid=v.appid, name=v.name, from_cache=v.from_cache)
            for k, v in (game.dlcs or {}).items()
        },
    )


def _candidate_to_model(c: DiscoveryResult) -> CandidateModel:
    assert c.appid is not None
    return CandidateModel(
        appid=c.appid,
        game_name=c.game_name,
        confidence=c.confidence,
        source=c.source.name if c.source else None,
    )


@router.post("/resolve", response_model=ResolvedGameModel)
async def resolve(body: ResolveRequest) -> ResolvedGameModel:
    if state.job_running:
        raise HTTPException(status_code=409, detail="A job is already running.")

    state.job_running = True
    try:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, partial(_do_resolve, body.path))
    except AppIDResolutionError as e:
        raise HTTPException(status_code=422, detail=str(e))
    finally:
        state.job_running = False


@router.get("/resolve/pending", response_model=PendingEventResponse)
async def get_pending() -> PendingEventResponse:
    """
    Returns the current pending event if the resolution thread is suspended
    waiting for a decision, or null if no decision is needed.
    """
    event = state.pending_event

    if event is None:
        return PendingEventResponse(event=None)

    if isinstance(event, AmbiguousMatchEvent):
        return PendingEventResponse(
            event=AmbiguousEventPayload(
                type="AmbiguousMatchEvent",
                candidates=[_candidate_to_model(c) for c in event.candidates],
                game_folder_name=event.game_folder_name,
            )
        )

    return PendingEventResponse(
        event=LowConfidenceEventPayload(
            type="LowConfidenceEvent",
            candidate=_candidate_to_model(event.candidate),
            threshold=event.threshold,
            game_folder_name=event.game_folder_name,
        )
    )


@router.post("/resolve/disambiguate")
async def disambiguate(body: DisambiguateRequest) -> dict:
    """
    Unblocks the resolution thread after an AmbiguousMatchEvent.
    The frontend submits the appid of the candidate the user chose.
    """
    event = state.pending_event
    if not isinstance(event, AmbiguousMatchEvent):
        raise HTTPException(status_code=409, detail="No disambiguation is pending.")

    chosen = next(
        (c for c in event.candidates if c.appid == body.appid),
        None,
    )
    if chosen is None:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    state.resolve_decision(chosen)
    return {"ok": True}


@router.post("/resolve/confirm")
async def confirm(body: ConfirmRequest) -> dict:
    """
    Unblocks the resolution thread after a LowConfidenceEvent.
    The frontend either accepts the candidate, rejects it, or supplies
    a manual appid to use instead.
    """
    event = state.pending_event
    if not isinstance(event, LowConfidenceEvent):
        raise HTTPException(status_code=409, detail="No confirmation is pending.")

    if body.accept:
        state.resolve_decision(event.candidate)
    elif body.manual_appid is not None:
        state.resolve_decision(
            DiscoveryResult(
                appid=body.manual_appid,
                source=ResolutionSource.MANUAL,
                confidence=1.0,
                game_name=None,
                user_selected=True,
            )
        )
    else:
        # User rejected with no alternative — resolve_decision(None) lets
        # the core raise AppIDNotFoundError.
        state.resolve_decision(None)

    return {"ok": True}
