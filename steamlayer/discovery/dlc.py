from __future__ import annotations

import json
import logging
import pathlib
import time

from .repository import AppIndexRepository
from .web import SteamWebClient

log = logging.getLogger("steamlayer.discovery.dlc")

CACHE_TTL = 86400 * 7  # 1 week


class DLCService:
    def __init__(
        self,
        repo: AppIndexRepository,
        web: SteamWebClient,
    ) -> None:
        self.repo = repo
        self.web = web

    def _read_cache(self, cache_path: pathlib.Path) -> dict[str | int, str]:
        if not cache_path.exists():
            return {}

        try:
            data = json.loads(cache_path.read_text(encoding="utf-8"))
            fetched_at = data.get("fetched_at", 0)

            if (time.time() - fetched_at) > CACHE_TTL:
                log.info("Found expired cache, skipping.")
                return {}

            dlcs = data.get("dlcs", {})
            if isinstance(dlcs, dict):
                return {int(k): str(v) for k, v in dlcs.items()}

        except Exception:
            return {}

        return {}

    def _write_cache(self, cache_path: pathlib.Path, dlcs: dict[int | str, str]) -> None:
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "fetched_at": int(time.time()),
                "dlcs": {str(k): v for k, v in dlcs.items()},
            }
            cache_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception:
            log.warning("Something went wrong while writing cache, skipping.")
            cache_path.unlink(missing_ok=True)

    def fetch(
        self,
        appid: int,
        *,
        cache_path: pathlib.Path | None = None,
        allow_network: bool = True,
    ) -> dict[str | int, str]:
        log.info(f"Fetching DLC metadata for AppID {appid}...")

        if cache_path and cache_path.exists():
            cached = self._read_cache(cache_path)
            if cached:
                log.info(f"Cache hit — loaded {len(cached)} DLC(s).")
                return cached

        if not allow_network:
            log.info("Network disabled; skipping DLC hydration.")
            return {}

        log.info("Cache miss — fetching DLC(s) from Steam API...")
        try:
            data = self.web.get_app_details(appid)

            app_data = data.get(str(appid), {})
            if not app_data.get("success"):
                return {}

            dlc_ids = app_data["data"].get("dlc", [])
            if not dlc_ids:
                return {}

            dlc_index = self.repo.get_dlc_index()

            final_dlcs: dict[str | int, str] = {}
            missing_ids: list[int] = []
            for d_id in dlc_ids:
                d_id_int = int(d_id)
                name = dlc_index.get(d_id_int)

                if name:
                    final_dlcs[d_id_int] = name
                else:
                    missing_ids.append(d_id_int)

            if missing_ids:
                log.info(f"Found {len(missing_ids)} missing DLCs: {missing_ids}")

            for m_id in missing_ids:
                try:
                    log.info(f"Fetching missing DLC {m_id} individually.")
                    m_data = self.web.get_app_details(m_id)
                    m_info = m_data.get(str(m_id), {}).get("data", {})
                    m_name = m_info.get("name")

                    if m_name:
                        log.info(f"Resolved missing DLC: {m_id} -> '{m_name}'")
                        final_dlcs[m_id] = m_name
                    else:
                        log.warning(f"DLC {m_id} returned no name, using fallback.")
                        final_dlcs[m_id] = f"DLC {m_id}"

                except Exception as e:
                    log.warning(f"Failed to fetch DLC {m_id}: {e}")
                    final_dlcs[m_id] = f"DLC {m_id}"

            if cache_path:
                self._write_cache(cache_path, final_dlcs)

            return final_dlcs

        except Exception as e:
            log.warning(f"DLC hydration failed: {e}")
            return {}
