from __future__ import annotations

import logging
import shutil

from .base import Bootstrapper

log = logging.getLogger("steamlayer.bootstrap.steamless")

REPO = "atom0s/Steamless"
RELEASES_API = f"https://api.github.com/repos/{REPO}/releases/latest"


class SteamlessBootstrapper(Bootstrapper):
    _name = "steamless"

    def _is_installed(self) -> bool:
        cli_exe = self._path / "Steamless.CLI.exe"
        return cli_exe.exists() and cli_exe.stat().st_size > 0

    def _get_latest_version(self) -> str | None:
        if not self._http:
            raise RuntimeError("Network access required but HTTP client is not available.")

        try:
            data: dict[str, str] = self._http.get(RELEASES_API).json()
            return data.get("tag_name")
        except Exception:
            log.warning("Could not fetch latest Steamless version from GitHub.")
            return None

    def _install(self) -> None:
        if not self._http:
            raise RuntimeError("Network access required but HTTP client is not available.")

        try:
            release_data = self._http.get(RELEASES_API).json()
            latest = release_data.get("tag_name")

            download_url = None
            for asset in release_data.get("assets", []):
                if asset["name"].endswith(".zip"):
                    download_url = asset["browser_download_url"]
                    break

            if not download_url:
                raise RuntimeError("Could not find a valid .zip asset in the latest Steamless release.")
        except Exception as e:
            raise RuntimeError(f"Failed to resolve Steamless download URL: {e}")

        data = self._download(download_url)
        self._reset_dir()

        extract_tmp = self._extract_archive(data, "steamless.zip")
        try:
            for item in extract_tmp.iterdir():
                if item.name == "steamless.zip":
                    continue

                dest = self._path / item.name
                if item.is_dir():
                    if dest.exists():
                        shutil.rmtree(dest)
                    shutil.copytree(item, dest)
                else:
                    shutil.move(str(item), dest)

            inner_dir = self._path / "Steamless"
            if not (self._path / "Steamless.CLI.exe").exists() and inner_dir.exists():
                for item in inner_dir.iterdir():
                    shutil.move(str(item), self._path / item.name)
                shutil.rmtree(inner_dir)

        finally:
            shutil.rmtree(extract_tmp, ignore_errors=True)

        if latest:
            self._save_version(latest)

        log.info(f"Steamless {latest} installed successfully.")
