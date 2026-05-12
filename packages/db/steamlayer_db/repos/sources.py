# packages/db/src/steamlayer_db/repos/sources.py
from __future__ import annotations

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from steamlayer_db.models import Source


class SourcesRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def all(self) -> list[Source]:
        result = await self._s.exec(select(Source).order_by(Source.name))
        return list(result.all())

    async def add(self, name: str, url: str) -> Source:
        source = Source(name=name, url=url)
        self._s.add(source)
        await self._s.commit()
        await self._s.refresh(source)
        return source

    async def set_enabled(self, id: int, enabled: bool) -> None:
        result = await self._s.exec(select(Source).where(Source.id == id))
        source = result.first()
        if source:
            source.enabled = enabled
            await self._s.commit()

    async def delete(self, id: int) -> None:
        result = await self._s.exec(select(Source).where(Source.id == id))
        source = result.first()
        if source:
            await self._s.delete(source)
            await self._s.commit()
