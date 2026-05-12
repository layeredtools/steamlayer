from __future__ import annotations

from datetime import datetime

from sqlmodel import select, col
from sqlmodel.ext.asyncio.session import AsyncSession

from steamlayer_db.models import Download


class DownloadsRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def create(
        self,
        source_url: str,
        appid: int | None = None,
        game_name: str | None = None,
        game_id: int | None = None,
        source_id: int | None = None,
        release_name: str | None = None,
    ) -> Download:
        download = Download(
            source_url=source_url,
            appid=appid,
            game_name=game_name,
            game_id=game_id,
            source_id=source_id,
            release_name=release_name,
        )
        self._s.add(download)
        await self._s.commit()
        await self._s.refresh(download)
        return download

    async def update_progress(
        self, id: int, progress: float, downloaded_bytes: int
    ) -> None:
        result = await self._s.exec(select(Download).where(Download.id == id))
        download = result.first()
        if download:
            download.progress = progress
            download.downloaded_bytes = downloaded_bytes
            download.status = "downloading"
            if not download.started_at:
                download.started_at = datetime.utcnow()
            await self._s.commit()

    async def set_status(
        self,
        id: int,
        status: str,
        error: str | None = None,
        local_path: str | None = None,
    ) -> Download | None:
        result = await self._s.exec(select(Download).where(Download.id == id))
        download = result.first()
        if download:
            download.status = status
            if error:
                download.error = error

            if local_path:
                download.local_path = local_path

            if status in ("done", "failed", "cancelled"):
                download.finished_at = datetime.utcnow()

            await self._s.commit()
            await self._s.refresh(download)
        return download

    async def all(self) -> list[Download]:
        result = await self._s.exec(
            select(Download).order_by(col(Download.created_at).desc())
        )
        return list(result.all())

    async def get(self, id: int) -> Download | None:
        result = await self._s.exec(select(Download).where(Download.id == id))
        return result.first()

    async def delete(self, id: int) -> None:
        result = await self._s.exec(select(Download).where(Download.id == id))
        download = result.first()
        if download:
            await self._s.delete(download)
            await self._s.commit()
