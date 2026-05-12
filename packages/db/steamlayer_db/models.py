# packages/db/src/steamlayer_db/models.py
from __future__ import annotations

from datetime import datetime
from sqlmodel import SQLModel, Field


class Game(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    appid: int
    name: str | None = None
    path: str = Field(unique=True)
    is_patched: bool = False
    added_at: datetime = Field(default_factory=datetime.utcnow)
    patched_at: datetime | None = None


class Source(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True)
    url: str
    enabled: bool = True


class Download(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    game_id: int | None = Field(default=None, foreign_key="game.id")
    appid: int | None = None
    game_name: str | None = None
    source_id: int | None = Field(default=None, foreign_key="source.id")
    source_url: str
    release_name: str | None = None
    status: str = "pending"
    progress: float = 0.0
    total_bytes: int | None = None
    downloaded_bytes: int = 0
    local_path: str | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    finished_at: datetime | None = None


class DownloadHistory(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    appid: int | None = None
    game_name: str | None = None
    source_name: str | None = None
    source_url: str
    release_name: str | None = None
    status: str
    total_bytes: int | None = None
    duration_seconds: float | None = None
    local_path: str | None = None
    error: str | None = None
    started_at: datetime | None = None
    finished_at: datetime = Field(default_factory=datetime.utcnow)
