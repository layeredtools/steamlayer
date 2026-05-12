from __future__ import annotations

from sqlmodel import select, col
from sqlmodel.ext.asyncio.session import AsyncSession

from steamlayer_db.models import Download, DownloadHistory


class HistoryRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def record(self, download: Download, source_name: str | None) -> None:
        duration = None
        if download.started_at and download.finished_at:
            duration = (download.finished_at - download.started_at).total_seconds()

        history = DownloadHistory(
            appid=download.appid,
            game_name=download.game_name,
            source_name=source_name,
            source_url=download.source_url,
            release_name=download.release_name,
            status=download.status,
            total_bytes=download.total_bytes,
            duration_seconds=duration,
            local_path=download.local_path,
            error=download.error,
            started_at=download.started_at,
        )
        self._s.add(history)
        await self._s.commit()

    async def all(self) -> list[DownloadHistory]:
        result = await self._s.exec(
            select(DownloadHistory).order_by(col(DownloadHistory.finished_at).desc())
        )
        return list(result.all())

    async def clear(self) -> None:
        result = await self._s.exec(select(DownloadHistory))
        for row in result.all():
            await self._s.delete(row)

        await self._s.commit()
