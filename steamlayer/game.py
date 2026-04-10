from __future__ import annotations

import logging
import pathlib
import shutil

from steamlayer.emulators import Emulator, EmulatorConfig
from steamlayer.fileops import SteamAPIDll

log = logging.getLogger("steamlayer." + __name__)

VAULT_NAME = "__original_files__"


class Game:
    def __init__(self, path: pathlib.Path, appid: int | None = None) -> None:
        self.appid = appid
        self.path = path
        self.dlcs: dict[int, str] = {}

    def find_steam_dlls(self) -> list[SteamAPIDll]:
        log.info("Searching for SteamAPI DLLs...")
        wanted = ("steam_api.dll", "steam_api64.dll")

        found_paths: list[pathlib.Path] = []
        seen: set[str] = set()
        for name in wanted:
            for p in self.path.rglob(name):
                key = str(p).lower()
                if key in seen:
                    continue

                if VAULT_NAME in key:
                    continue

                if p.name.lower() != name:
                    continue

                found_paths.append(p)
                seen.add(key)

        dlls = [SteamAPIDll(p) for p in found_paths]
        for dll in dlls:
            log.info(f"Found {dll}")

        log.info(f"Found {len(dlls)} SteamAPI DLLs in '{self.path}'.")
        return dlls


class GamePatcher:
    def __init__(self, game: Game, emulator: Emulator, *, config: EmulatorConfig, dry_run: bool = False) -> None:
        self.game = game
        self.config = config
        self.emulator = emulator
        self.dry_run = dry_run
        self.vault_root = self.game.path / VAULT_NAME

    def run(self) -> None:
        if self.vault_root.exists() and any(self.vault_root.iterdir()):
            log.warning("---")
            log.warning("!!! PREVIOUS BACKUP DETECTED !!!")
            log.warning(f"A vault already exists at: {self.vault_root}")
            log.warning("The patcher will proceed, but it will NOT overwrite existing backups.")
            log.warning("This ensures your original retail DLLs are never replaced by patched ones.")
            log.warning("---")

        dry_prefix = "[DRY RUN] " if self.dry_run else ""
        game_name = self.game.path.name
        appid = self.game.appid if self.game.appid is not None else "unknown"

        log.info(
            f"{dry_prefix}Starting patch "
            f"(Game='{game_name}', AppID={appid}, DryRun={self.dry_run}) "
            f"using '{self.emulator}'"
        )

        dlls = self.game.find_steam_dlls()
        if not dlls:
            raise FileNotFoundError("No Steam API DLLs found in game directory.")

        for dll in dlls:
            relative_path = dll.file.relative_to(self.game.path)
            vault_dest = self.vault_root / relative_path
            dll.set_backup_destination(vault_dest)

        if self.dry_run:
            patched_dlls = dlls  # used for logging at the end
            for dll in dlls:
                log.info(f"[DRY RUN] Would vault original to: {dll.backup_path}")
                log.info(f"[DRY RUN] Would overwrite: {dll.file}")

            for target_dir in {d.file.parent for d in dlls}:
                log.info(
                    f"[DRY RUN] Would configure '{target_dir}' using the following flags: "
                    f"(APPID={self.game.appid} DLLS={dlls} DLCS={self.game.dlcs}). "
                    f"User-specific information would also be correctly written."
                )

        else:
            patched_dlls = self.emulator.patch_game(dlls=dlls)
            try:
                self.emulator.create_config_files(
                    config=self.config,
                    appid=self.game.appid,
                    game_path=self.game.path,
                    dll_paths=[d.file for d in patched_dlls],
                )
            except Exception as e:
                log.error(
                    f"Config creation failed: {e}. The DLL patch was still applied "
                    "— the game may still work with default settings."
                )

        dlc_count = len(self.game.dlcs) if self.game.dlcs else 0
        dll_count = len(patched_dlls)

        log.info(f"{dry_prefix}Patch completed successfully (AppID={appid}, DLLs={dll_count}, DLCs={dlc_count})")


class GameRestorer:
    def __init__(self, game: Game, emulator: Emulator, *, dry_run: bool = False) -> None:
        self.game = game
        self.emulator = emulator
        self.dry_run = dry_run

        self.vault_root = self.game.path / VAULT_NAME

    def _is_vault_empty(self, path: pathlib.Path) -> bool:
        return not any(p.is_file() for p in path.rglob("*"))

    def run(self) -> None:
        dry_prefix = "[DRY RUN] " if self.dry_run else ""
        log.info(f"{dry_prefix}Starting restoration for '{self.game.path}'...")

        if not self.vault_root.exists():
            log.error(f"No vault found at '{self.vault_root}'. Cannot restore.")
            return

        all_vaulted = list(self.vault_root.rglob("steam_api*.dll"))
        if not all_vaulted:
            log.error("Vault exists but contains no DLLs to restore.")
            return

        restored_successfully: list[tuple[SteamAPIDll, pathlib.Path]] = []
        restoration_failed = False

        for vaulted_path in all_vaulted:
            rel = vaulted_path.relative_to(self.vault_root)
            original_dest = self.game.path / rel

            dll = SteamAPIDll(original_dest)
            dll.set_backup_destination(vaulted_path)

            if self.dry_run:
                log.info(f"[DRY RUN] Would restore {rel} to {original_dest}")
                continue

            try:
                log.info(f"Trying to restore {dll}...")
                current_backup = dll.backup_path

                # delete_backup=False preserves the vault in case a later DLL fails,
                # so --restore can be re-run safely from a clean state.
                dll.restore(delete_backup=False)

                restored_successfully.append((dll, current_backup))
                settings_dir = original_dest.parent / "steam_settings"
                if settings_dir.exists():
                    try:
                        shutil.rmtree(settings_dir)
                    except Exception as e:
                        log.warning(f"Could not remove steam_settings in '{original_dest.parent}': {e}. Skipping...")

            except Exception as e:
                log.error(f"CRITICAL: Failed to restore {rel}: {e}")
                restoration_failed = True
                break

        if restoration_failed and not self.dry_run:
            log.error(
                "Restoration incomplete. "
                f"{len(restored_successfully)} DLL(s) were restored successfully before the failure. "
                "The vault is preserved — you can re-run --restore to try again."
            )
            return

        if not self.dry_run:
            for _, vault_path in restored_successfully:
                try:
                    vault_path.unlink(missing_ok=True)
                except Exception as e:
                    log.warning(f"Could not delete vault file '{vault_path.name}': {e}")

            trash_files = self.emulator.config_files
            for trash in trash_files:
                for t_path in self.game.path.rglob(trash):
                    if VAULT_NAME not in str(t_path):
                        t_path.unlink(missing_ok=True)
                        log.info(f"Deleted {t_path}.")

            if self._is_vault_empty(self.vault_root):
                try:
                    shutil.rmtree(self.vault_root)
                    log.info("Vault cleared and removed.")
                except Exception as e:
                    log.warning(f"Could not remove vault directory: {e}")
            else:
                log.warning("Vault is not empty after cleanup — some files may not have been deleted.")

        log.info(f"{dry_prefix}Restoration completed successfully.")
