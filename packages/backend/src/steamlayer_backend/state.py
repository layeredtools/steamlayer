from __future__ import annotations

import asyncio
import threading
from typing import TYPE_CHECKING, cast

from steamlayer_core.domain.models import DiscoveryResult, SteamlayerOptions

if TYPE_CHECKING:
    from steamlayer_core.events import ResolutionEvent


class AppState:
    """
    Single shared state instance for the lifetime of the backend process.

    Holds:
    - The current SteamlayerOptions and allow_network flag (user settings)
    - A flag indicating whether a job is currently running
    - An asyncio.Queue for streaming progress events to the WebSocket
    - A threading.Event bridge for suspending the resolution thread while
      waiting for the frontend to submit a disambiguation or confirmation
      decision
    """

    def __init__(self) -> None:
        self.options: SteamlayerOptions = SteamlayerOptions()
        self.allow_network: bool = True
        self.job_running: bool = False
        self.progress_queue: asyncio.Queue[dict] = asyncio.Queue()

        # Pending event — set while the resolution thread is suspended
        # waiting for a frontend decision.
        self.pending_event: ResolutionEvent | None = None

        # Threading primitives that bridge the sync core with async FastAPI.
        # The resolution thread blocks on _decision_event.wait(); the FastAPI
        # route sets _decision_result and then fires the event to unblock it.
        self._decision_event: threading.Event = threading.Event()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._decision_result: object = None

    def push_progress(self, step: str, detail: str) -> None:
        """Enqueue a progress event for the WebSocket handler to forward."""
        assert self._loop
        self._loop.call_soon_threadsafe(
            self.progress_queue.put_nowait,
            {"event": step, "detail": detail},
        )

    def make_progress_callback(self):
        """Returns a ProgressCallback compatible with steamlayer-core's protocol."""

        def _callback(step: str, detail: str) -> None:
            self.push_progress(step, detail)

        return _callback

    def set_pending(self, event: ResolutionEvent) -> None:
        """
        Called by a handler running inside the resolution thread.
        Stores the event and resets the decision gate so the thread can
        block on it, then notifies the frontend via the progress queue.
        """
        self.pending_event = event
        self._decision_result = None
        self._decision_event.clear()
        self.push_progress("pending_decision", event.__class__.__name__)

    def wait_for_decision(self) -> DiscoveryResult:
        """
        Blocks the calling (resolution) thread until the frontend POSTs a
        decision. Returns whatever was stored by resolve_decision().
        """
        self._decision_event.wait()
        return cast(DiscoveryResult, self._decision_result)

    def resolve_decision(self, result: object) -> None:
        """
        Called by the FastAPI route when the frontend submits a decision.
        Stores the result and unblocks the resolution thread.
        """
        self._decision_result = result
        self.pending_event = None
        self._decision_event.set()


# Module-level singleton — imported directly by routers and the WS handler.
state = AppState()
