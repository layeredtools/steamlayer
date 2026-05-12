# packages/db/src/steamlayer_db/repos/games.py
from __future__ import annotations

from datetime import datetime

from sqlmodel import select, col
from sqlmodel.ext.asyncio.session import AsyncSession

from steamlayer_db.models import Game


class GamesRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def upsert(self, appid: int, name: str | None, path: str) -> Game:
        result = await self._s.exec(select(Game).where(Game.path == path))
        game = result.first()
        if game:
            game.appid = appid
            game.name = name
        else:
            game = Game(appid=appid, name=name, path=path)
            self._s.add(game)

        await self._s.commit()
        await self._s.refresh(game)
        return game

    async def set_patched(self, path: str, patched: bool) -> None:
        result = await self._s.exec(select(Game).where(Game.path == path))
        game = result.first()
        if game:
            game.is_patched = patched
            game.patched_at = datetime.utcnow() if patched else None
            await self._s.commit()

    async def get_by_path(self, path: str) -> Game | None:
        result = await self._s.exec(select(Game).where(Game.path == path))
        return result.first()

    async def all(self) -> list[Game]:
        result = await self._s.exec(select(Game).order_by(col(Game.added_at).desc()))
        return list(result.all())

    async def delete(self, id: int) -> None:
        result = await self._s.exec(select(Game).where(Game.id == id))
        game = result.first()
        if game:
            await self._s.delete(game)
            await self._s.commit()
