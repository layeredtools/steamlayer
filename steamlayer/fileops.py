from __future__ import annotations

import logging
import pathlib
import shutil
from typing import Literal

log = logging.getLogger("steamlayer." + __name__)


class BackedUpFile:
    def __init__(self, file: pathlib.Path) -> None:
        self.file = file
        self._custom_backup_path: pathlib.Path | None = None

    def __repr__(self) -> str:
        arch = getattr(self, "architecture", "N/A")
        return f"{self.__class__.__name__}({self.file.name}, arch={arch})"

    @property
    def backup_path(self) -> pathlib.Path:
        if self._custom_backup_path:
            return self._custom_backup_path

        # If not injected by GamePatcher, just do a "dumb" backup and not use our vault.
        return self.file.parent / f"{self.file.name}.bkp"

    def set_backup_destination(self, path: pathlib.Path) -> None:
        """Sets the specific location where this file should be vaulted."""
        self._custom_backup_path = path

    def backup(self) -> pathlib.Path:
        dest = self.backup_path
        if dest.exists() and dest.stat().st_size > 0:
            log.info(f"Backup already exists for '{self.file.name}', skipping.")
            return dest

        dest.parent.mkdir(parents=True, exist_ok=True)

        tmp = dest.with_suffix(".tmp")
        try:
            shutil.copy2(self.file, tmp)
            tmp.replace(dest)
        except Exception:
            tmp.unlink(missing_ok=True)
            raise

        log.info(f"Successfully backed up: '{self.file.name}' -> '{dest}'")
        return dest

    def get_backup(self) -> pathlib.Path | None:
        backup = self.backup_path
        if backup.exists() and backup.stat().st_size > 0:
            return backup
        return None

    def restore(self, *, delete_backup: bool = False) -> None:
        backup = self.get_backup()
        if backup is None:
            raise FileNotFoundError(f"Could not find a backup for {self.file}")

        tmp = self.file.with_suffix(".tmp")
        try:
            shutil.copy2(backup, tmp)
            tmp.replace(self.file)
        except Exception:
            tmp.unlink(missing_ok=True)
            raise

        log.info(f"Successfully restored the file '{self.file}' using backup '{backup}'.")
        if delete_backup:
            log.info("Deleting backup after restoring...")
            backup.unlink()


class SteamAPIDll(BackedUpFile):
    @property
    def architecture(self) -> Literal["x32", "x64"]:
        return "x64" if "64" in self.file.name else "x32"
