from __future__ import annotations

import logging
import pathlib
import shutil
from typing import Any

from steamlayer.emulators import Emulator
from steamlayer.emulators.goldberg.config import GoldbergConfig
from steamlayer.fileops import SteamAPIDll

log = logging.getLogger("steamlayer." + __name__)


class Goldberg(Emulator):
    def __init__(self, path: pathlib.Path) -> None:
        self._path = path

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(path={self.path})"

    @property
    def name(self) -> str:
        return "Goldberg"

    @property
    def path(self) -> pathlib.Path:
        return self._path

    @property
    def x32(self) -> pathlib.Path:
        return self._path / "regular" / "x32" / "steam_api.dll"

    @property
    def x64(self) -> pathlib.Path:
        return self._path / "regular" / "x64" / "steam_api64.dll"

    @property
    def settings_dir_name(self) -> str:
        return "steam_settings"

    @property
    def config_files(self) -> list[str]:
        return ["steam_appid.txt", "DLC.txt", "configs.user.ini", "configs.app.ini"]

    def validate(self) -> None:
        missing = [p for p in (self.x32, self.x64) if not p.exists()]
        if missing:
            raise FileNotFoundError(f"Goldberg binaries not found: {[str(p) for p in missing]}")
        log.info("Goldberg binaries validated.")

    def patch_game(self, *, dlls: list[SteamAPIDll]) -> list[SteamAPIDll]:
        log.info("Patching game DLLs...")
        patched: list[SteamAPIDll] = []
        try:
            for dll in dlls:
                log.info(f"Patching {dll.file} ({dll.architecture})...")
                dll.backup()

                src = self.x64 if dll.architecture == "x64" else self.x32
                shutil.copy2(src, dll.file)
                patched.append(dll)

                log.info(f"Patched {dll.file} successfully.")
        except Exception:
            log.warning("Patching failed mid-loop — rolling back...")
            for dll in patched:
                try:
                    dll.restore(delete_backup=True)
                    log.info(f"Rolled back {dll.file}.")
                except Exception as e:
                    log.error(f"Failed to roll back {dll.file}: {e}")
            raise
        log.info(f"Patched {len(patched)} DLL(s) successfully.")
        return patched

    def create_config_files(
        self,
        *,
        config: GoldbergConfig,  # type: ignore
        appid: int | None,
        game_path: pathlib.Path,
        dll_paths: list[pathlib.Path],
        **kwargs: Any,  # mypy bitching
    ) -> None:
        use_legacy_dlls = kwargs.get("use_legacy_dlls", False)  # type: bool
        if appid is None:
            log.warning(
                "No AppID provided. Proceeding without 'steam_appid.txt'. The game will rely on Goldberg's fallback."
            )

        target_dirs = {p.parent for p in dll_paths}
        for target_dir in target_dirs:
            steam_settings_dir = target_dir / self.settings_dir_name
            config.write(steam_settings_dir, legacy_dlcs=use_legacy_dlls)
            if appid is not None:
                (steam_settings_dir / "steam_appid.txt").write_text(str(appid), encoding="utf-8")
                log.info(f"Written steam_appid.txt to {steam_settings_dir}.")
            log.info(f"Configured folder: {target_dir}")

        if appid is not None:
            (game_path / "steam_appid.txt").write_text(str(appid), encoding="utf-8")
            log.info(f"Written steam_appid.txt to game root '{game_path}'.")
