from __future__ import annotations

import logging
import pathlib
import shutil
import subprocess
import time

from steamlayer import state
from steamlayer.http_client import HTTPClient, RequestError

log = logging.getLogger("steamlayer.bootstrap")

UPDATE_TTL = 86400  # 1 day


class Bootstrapper:
    _name = ""

    def __init__(self, path: pathlib.Path, http: HTTPClient | None) -> None:
        self._path = path
        self._http = http
        self._cached_latest: str | None = None

    def ensure(self, *, allow_network: bool = True) -> None:
        if not self._is_installed():
            if not allow_network:
                raise RuntimeError(f"{self.__class__.__name__} is not installed and network is disabled.")

            log.info(f"Installing {self.__class__.__name__}...")
            self._install()

        elif allow_network and self._should_update():
            log.info(f"Updating {self.__class__.__name__}...")
            self._install()

        else:
            log.debug(f"{self.__class__.__name__} already installed and up to date.")

    def _is_installed(self) -> bool:
        raise NotImplementedError

    def _install(self) -> None:
        raise NotImplementedError

    def _get_latest_version(self) -> str | None:
        return None

    def _get_installed_version(self) -> str | None:
        return state.get(self._name, "version", None)

    def _get_last_checked_time(self) -> int:
        return state.get(self._name, "last_check", 0)

    def _save_version(self, version: str) -> None:
        return state.update_section(self._name, version=version, last_check=time.time())

    def _should_update(self) -> bool:
        elapsed = time.time() - self._get_last_checked_time()
        if elapsed < UPDATE_TTL:
            log.debug("%s metadata is fresh (age: %.1fh). Skipping check.", self._name, elapsed / 3600)
            return False

        latest = self._get_latest_version()
        self._cached_latest = latest
        if latest is None:
            return False

        installed = self._get_installed_version()
        if installed is None:
            log.info(f"{self.__class__.__name__}: no version file found, assuming update needed.")
            return True

        if latest != installed:
            log.info(f"{self.__class__.__name__} update available: {installed} → {latest}")
            return True

        log.debug(f"{self.__class__.__name__} is up to date ({installed}).")
        return False

    def _find_7zip(self) -> str:
        candidate = self._path.parent / "7zip" / "7z.exe"
        if candidate.exists():
            return str(candidate)

        found = shutil.which("7z")
        if found:
            return found

        raise FileNotFoundError("7-Zip not found.")

    def _extract_archive(
        self,
        data: bytes,
        archive_name: str,
        targets: list[str] | None = None,
    ) -> pathlib.Path:
        """
        Writes `data` to a temp dir, extracts it with 7z, and returns the
        temp path for the caller to move files out of. Caller is responsible
        for cleanup. Raises RuntimeError on extraction failure.
        """
        seven_zip = self._find_7zip()

        extract_tmp = self._path / "_tmp"
        extract_tmp.mkdir(parents=True, exist_ok=True)

        archive_path = extract_tmp / archive_name
        archive_path.write_bytes(data)

        cmd = [seven_zip, "x", str(archive_path), "-o" + str(extract_tmp), "-y"]
        if targets:
            cmd += targets

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            shutil.rmtree(extract_tmp, ignore_errors=True)
            hint = ""
            if "virus" in result.stderr.lower() or "unwanted" in result.stderr.lower():
                hint = (
                    f"\n\nWindows Defender likely quarantined the file. "
                    f"Add an exclusion for this specific folder and re-run:\n"
                    f"  {self._path.parent}"
                )
            raise RuntimeError(f"7-Zip extraction failed:\n{result.stderr}{hint}")
        return extract_tmp

    def _download(self, url: str) -> bytes:
        if not self._http:
            raise RuntimeError("Network access required but HTTP client is not available.")

        log.debug(f"Downloading from '{url}'...")
        try:
            return self._http.get(url).content  # type: ignore
        except RequestError as e:
            raise RuntimeError(f"Failed to download '{url}': {e}") from e

    def _reset_dir(self) -> None:
        if self._path.exists():
            shutil.rmtree(self._path)
        self._path.mkdir(parents=True, exist_ok=True)

    def is_available(self) -> bool:
        return self._is_installed()
