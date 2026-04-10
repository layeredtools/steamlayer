from __future__ import annotations

import logging
import pathlib
import re
import shutil
import subprocess

from .base import Bootstrapper

log = logging.getLogger("steamlayer.bootstrap.7zip")

DOWNLOAD_PAGE = "https://www.7-zip.org/download.html"
EXTRA_URL_TEMPLATE = "https://www.7-zip.org/a/7z{version}-extra.7z"


class SevenZipBootstrapper(Bootstrapper):
    def _is_installed(self) -> bool:
        return (self._path / "7z.exe").exists()

    def _get_latest_version(self) -> str | None:
        if not self._http:
            raise RuntimeError("Network access required but HTTP client is not available.")

        try:
            log.debug("Fetching latest 7-Zip version from 7-zip.org...")
            html = self._http.get(DOWNLOAD_PAGE).text
            match = re.search(r"7z(\d{4,})-extra\.7z", html)
            if not match:
                log.warning("Could not determine latest 7-Zip version from download page.")
                return None

            version = match.group(1)
            log.debug(f"Latest 7-Zip version: {version}")
            return version

        except Exception:
            log.warning("Could not fetch latest 7-Zip version.")
            return None

    def _find_system_7z(self) -> str | None:
        candidates = [
            shutil.which("7z"),
            shutil.which("7za"),
            shutil.which("7zz"),
            r"C:\Program Files\7-Zip\7z.exe",
            r"C:\Program Files (x86)\7-Zip\7z.exe",
        ]
        for path in candidates:
            if path and pathlib.Path(path).exists():
                return str(path)
        return None

    def _install(self) -> None:
        system_7z = self._find_system_7z()
        if not system_7z:
            raise RuntimeError("Cannot bootstrap 7-Zip: no existing 7z found in PATH or standard install locations.")

        latest = self._get_latest_version()
        if not latest:
            raise RuntimeError("Could not determine latest 7-Zip version.")

        url = EXTRA_URL_TEMPLATE.format(version=latest)
        data = self._download(url)

        # Can't use _extract_archive here since 7z isn't bootstrapped yet —
        # we use the system 7z directly for this one-time extraction.
        with __import__("tempfile").TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            archive = tmp_path / "7zip.7z"
            archive.write_bytes(data)

            result = subprocess.run(
                [system_7z, "x", str(archive), f"-o{tmp_path}", "-y"],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise RuntimeError(f"7-Zip extraction failed:\n{result.stderr}")

            found = next((p for p in tmp_path.rglob("7za.exe")), None)
            if not found:
                raise FileNotFoundError(
                    f"7za.exe not found in extracted archive. Contents: "
                    f"{[str(p.relative_to(tmp_path)) for p in tmp_path.rglob('*')]}"
                )

            self._reset_dir()
            shutil.copy2(found, self._path / "7z.exe")

        self._save_version(latest)
        log.info(f"7-Zip {latest} installed at '{self._path}'.")
