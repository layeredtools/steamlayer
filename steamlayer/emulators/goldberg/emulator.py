from __future__ import annotations

import logging
import pathlib
import shutil
from typing import TYPE_CHECKING, Any, cast

from steamlayer.emulators import Emulator, EmulatorConfig
from steamlayer.fileops import SteamAPIDll

if TYPE_CHECKING:
    pass

log = logging.getLogger("steamlayer." + __name__)


class Goldberg(Emulator):
    """
    Goldberg Steam emulator wrapper.

    Responsible for:
    - Validating Goldberg binaries are present
    - Patching game DLLs with Goldberg versions
    - Writing configuration files (steam_settings/)
    """

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
        """Config files written by this emulator — used by restore to clean up."""
        return [
            "steam_appid.txt",
            "DLC.txt",
            "configs.user.ini",
            "configs.app.ini",
        ]

    def validate(self) -> None:
        """
        Raise FileNotFoundError if the Goldberg binaries are missing.
        """
        missing = [p for p in (self.x32, self.x64) if not p.exists()]
        if missing:
            raise FileNotFoundError(f"Goldberg binaries not found: {[str(p) for p in missing]}")
        log.info("Goldberg binaries validated.")

    def patch_game(self, *, dlls: list[SteamAPIDll]) -> list[SteamAPIDll]:
        """
        Replace game Steam DLLs with Goldberg versions.

        For each DLL:
        1. Back up the original to the vault.
        2. Copy the matching Goldberg DLL (x32 or x64).

        On failure mid-loop, rolls back all already-patched DLLs.

        Returns:
            List of successfully patched DLLs.
        """
        log.info("Patching game DLLs...")
        patched: list[SteamAPIDll] = []

        try:
            for dll in dlls:
                log.info("Patching %s (%s)...", dll.file, dll.architecture)
                dll.backup()
                src = self.x64 if dll.architecture == "x64" else self.x32
                shutil.copy2(src, dll.file)
                patched.append(dll)
                log.info("Patched %s successfully.", dll.file)

        except Exception:
            log.warning("Patching failed mid-loop — rolling back...")
            for dll in patched:
                try:
                    dll.restore(delete_backup=True)
                    log.info("Rolled back %s.", dll.file)
                except Exception as e:
                    log.error("Failed to roll back %s: %s", dll.file, e)
            raise

        log.info("Patched %d DLL(s) successfully.", len(patched))
        return patched

    def create_config_files(
        self,
        *,
        config: EmulatorConfig,
        appid: int | None,
        game_path: pathlib.Path,
        dll_paths: list[pathlib.Path],
        **kwargs: Any,
    ) -> None:
        """
        Write Goldberg configuration files next to each patched DLL.

        For every directory that contains a patched DLL this creates a
        ``steam_settings/`` folder and calls ``config.write()`` to populate it.
        Whether to write ``steam_appid.txt`` and which DLC format to use are
        both controlled by fields on *config* (``write_steam_appid`` and
        ``legacy_dlcs`` respectively) — no extra kwargs needed.

        Args:
            config:     GoldbergConfig instance (account_name, language, dlcs, flags).
            appid:      Steam AppID, or None if not discovered.
            game_path:  Root directory of the game (steam_appid.txt goes here too).
            dll_paths:  Paths to the patched DLL files.
        """
        from steamlayer.emulators.goldberg.config import GoldbergConfig

        gb_config = cast(GoldbergConfig, config)

        if appid is None:
            log.warning(
                "No AppID provided — proceeding without steam_appid.txt. "
                "The game will rely on Goldberg's fallback."
            )

        target_dirs = {p.parent for p in dll_paths}
        for target_dir in target_dirs:
            steam_settings_dir = target_dir / self.settings_dir_name
            gb_config.write(steam_settings_dir)

            if appid is not None and gb_config.write_steam_appid:
                (steam_settings_dir / "steam_appid.txt").write_text(str(appid), encoding="utf-8")
                log.info("Written steam_appid.txt to %s.", steam_settings_dir)

            log.info("Configured folder: %s", target_dir)

        if appid is not None and gb_config.write_steam_appid:
            (game_path / "steam_appid.txt").write_text(str(appid), encoding="utf-8")
            log.info("Written steam_appid.txt to game root '%s'.", game_path)
