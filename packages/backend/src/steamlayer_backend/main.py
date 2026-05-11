from __future__ import annotations

import asyncio
import logging

from steamlayer_backend.routers import dlcs, patch
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from steamlayer_backend.routers import settings
from steamlayer_backend.ws.progress import router as ws_router
from steamlayer_backend.state import state
from steamlayer_backend.routers import resolve

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("steamlayer_backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    def _capture_loop():
        state._loop = asyncio.get_running_loop()
    _capture_loop()
    yield

app = FastAPI(
    title="SteamLayer Backend", 
    version="0.1.0",
    lifespan=lifespan
)

# Electron's renderer runs on a different origin during development,
# so we allow localhost for all ports. In production the renderer is
# loaded as a file:// URL, which also requires wildcard origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resolve.router)
app.include_router(patch.router)
app.include_router(dlcs.router)
app.include_router(settings.router)
app.include_router(ws_router)


@app.get("/health")
async def health() -> dict:
    """Polled by Electron's backend.ts to know when the process is ready."""
    return {"status": "ok"}


@app.exception_handler(Exception)
async def generic_exception_handler(request, exc: Exception) -> JSONResponse:
    log.exception("Unhandled exception: %s", exc)
    return JSONResponse(status_code=500, content={"detail": str(exc)})


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=58732)
    args = parser.parse_args()
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="info")

if __name__ == "__main__":
    main()