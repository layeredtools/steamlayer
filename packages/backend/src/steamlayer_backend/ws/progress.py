from __future__ import annotations

import logging

from backend.state import state
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

log = logging.getLogger("steamlayer_backend.ws")
router = APIRouter()


@router.websocket("/ws/progress")
async def progress(websocket: WebSocket) -> None:
    await websocket.accept()
    log.info("WebSocket client connected")
    try:
        while True:
            # Block until a progress event is enqueued by a running job,
            # then forward it to the client immediately.
            event = await state.progress_queue.get()
            await websocket.send_json(event)
    except WebSocketDisconnect:
        log.info("WebSocket client disconnected")
    except Exception as e:
        log.exception("WebSocket error: %s", e)
    finally:
        while not state.progress_queue.empty():
            state.progress_queue.get_nowait()
