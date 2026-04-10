from __future__ import annotations

import json
import logging
import pathlib
import time
from collections.abc import Callable
from typing import Any

from steamlayer.http_client import HTTPClient, RequestError

log = logging.getLogger("steamlayer.discovery.repository")

INDEX_TTL = 86400 * 7  # 1 week


class AppIndexRepository:
    APP_LIST_URL = "https://raw.githubusercontent.com/jsnli/steamappidlist/refs/heads/master/data/games_appid.json"
    DLC_LIST_URL = "https://raw.githubusercontent.com/jsnli/steamappidlist/refs/heads/master/data/dlc_appid.json"

    def __init__(
        self,
        http: HTTPClient,
        data_dir: pathlib.Path | None = None,
    ) -> None:
        self._http = http
        self.data_dir = data_dir or pathlib.Path.home() / ".steamlayer"
        self.app_list_path = self.data_dir / "steam_app_index.json"
        self.dlc_index_path = self.data_dir / "steam_dlc_index.json"
        self._app_index: dict[str, int] = {}
        self._dlc_index: dict[int, str] = {}

    def _ensure_index(self, path: pathlib.Path, url: str, label: str) -> bool:
        file_exists = path.exists()
        should_update = not file_exists

        if file_exists and (time.time() - path.stat().st_mtime) > INDEX_TTL:
            log.info(f"Local {label} index is outdated, attempting refresh...")
            should_update = True

        if should_update:
            try:
                log.info(f"Downloading community {label} index mirror...")
                self._http.download(url, path)
                log.info(f"Successfully updated {label} index.")
                return True

            except RequestError as e:
                log.warning(f"Could not update {label} mirror: {e}.")
                return file_exists
        return True

    def _load_index(
        self,
        path: pathlib.Path,
        url: str,
        label: str,
        transform: Callable[[list[Any]], dict],
    ) -> dict:
        if not self._ensure_index(path, url, label):
            return {}
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            return transform(raw)
        except Exception as e:
            log.warning(f"{label} index load error: {e}. Purging.")
            path.unlink(missing_ok=True)
            return {}

    def get_app_index(self) -> dict[str, int]:
        if not self._app_index:
            self._app_index = self._load_index(
                self.app_list_path,
                self.APP_LIST_URL,
                "App",
                lambda raw: {str(a["name"]).lower(): int(a["appid"]) for a in raw if a.get("name") and a.get("appid")},
            )
        return self._app_index

    def get_dlc_index(self) -> dict[int, str]:
        if not self._dlc_index:
            self._dlc_index = self._load_index(
                self.dlc_index_path,
                self.DLC_LIST_URL,
                "DLC",
                lambda raw: {int(d["appid"]): str(d["name"]) for d in raw if d.get("appid") and d.get("name")},
            )
        return self._dlc_index
