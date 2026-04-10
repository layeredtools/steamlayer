from __future__ import annotations

import logging
import pathlib
import shutil

from .base import Bootstrapper

log = logging.getLogger("steamlayer.bootstrap.goldberg")

REPO = "Detanup01/gbe_fork"
ASSET_NAME = "emu-win-release.7z"
RELEASE_URL = f"https://github.com/{REPO}/releases/latest/download/{ASSET_NAME}"
RELEASES_API = f"https://api.github.com/repos/{REPO}/releases/latest"

_EXTRACT_TARGETS = [
    "release/regular/x32/steam_api.dll",
    "release/regular/x64/steam_api64.dll",
]


class GoldbergBootstrapper(Bootstrapper):
    def _is_installed(self) -> bool:
        x32 = self._path / "regular" / "x32" / "steam_api.dll"
        x64 = self._path / "regular" / "x64" / "steam_api64.dll"
        return all(p.exists() and p.stat().st_size > 0 for p in (x32, x64))

    def _get_latest_version(self) -> str | None:
        if not self._http:
            raise RuntimeError("Network access required but HTTP client is not available.")
        try:
            data: dict[str, str] = self._http.get(RELEASES_API).json()
            return data.get("tag_name")
        except Exception:
            log.warning("Could not fetch latest Goldberg version from GitHub.")
            return None

    def _install(self) -> None:
        latest = self._get_latest_version()
        data = self._download(RELEASE_URL)
        self._reset_dir()

        extract_tmp = self._extract_archive(data, "goldberg.7z", _EXTRACT_TARGETS)
        try:
            for arc_path in _EXTRACT_TARGETS:
                src = extract_tmp / arc_path
                dest = self._path / pathlib.Path(arc_path).relative_to("release")
                dest.parent.mkdir(parents=True, exist_ok=True)
                if not src.exists():
                    raise FileNotFoundError(f"Missing '{arc_path}' after extraction.")
                shutil.move(str(src), dest)
        finally:
            shutil.rmtree(extract_tmp, ignore_errors=True)

        if latest:
            self._save_version(latest)
        log.info(f"Goldberg {latest} installed.")
