from __future__ import annotations

import logging
import pathlib
import shutil
import subprocess

from steamlayer.http_client import HTTPClient, RequestError

log = logging.getLogger("steamlayer.bootstrap")

VERSION_FILE = "_version.txt"


class Bootstrapper:
    def __init__(self, path: pathlib.Path, http: HTTPClient | None) -> None:
        self._path = path
        self._http = http

    def ensure(self) -> None:
        if not self._is_installed():
            log.info(f"Installing {self.__class__.__name__}...")
            self._install()
        elif self._should_update():
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
        version_file = self._path / VERSION_FILE
        if version_file.exists():
            return version_file.read_text(encoding="utf-8").strip()
        return None

    def _save_version(self, version: str) -> None:
        (self._path / VERSION_FILE).write_text(version, encoding="utf-8")

    def _should_update(self) -> bool:
        latest = self._get_latest_version()
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
