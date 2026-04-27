from __future__ import annotations

import configparser
import logging
import pathlib
from dataclasses import dataclass
from typing import Self

from steamlayer.config.defaults import DEFAULTS, VALID_LANGUAGES, GoldbergConfigDict
from steamlayer.emulators import EmulatorConfig

log = logging.getLogger("steamlayer." + __name__)


def _atomic_write_configparser(cfg: configparser.RawConfigParser, dest_path: pathlib.Path) -> None:
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest_path.with_name(dest_path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        cfg.write(f)
    tmp.replace(dest_path)


def _atomic_write_text(text: str, dest_path: pathlib.Path) -> None:
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest_path.with_name(dest_path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(dest_path)


@dataclass
class GoldbergConfig(EmulatorConfig):
    _GOLDBERG_DEFAULTS = DEFAULTS["goldberg"]

    account_name: str = _GOLDBERG_DEFAULTS["account_name"]
    language: str = _GOLDBERG_DEFAULTS["language"]
    legacy_dlcs: bool = _GOLDBERG_DEFAULTS["legacy_dlcs"]
    unlock_all_dlcs: bool = _GOLDBERG_DEFAULTS["unlock_all_dlcs"]
    write_steam_appid: bool = _GOLDBERG_DEFAULTS["write_steam_appid"]
    preserve_user_cfg: bool = _GOLDBERG_DEFAULTS["preserve_user_cfg"]

    @classmethod
    def from_config(cls, config_dict: GoldbergConfigDict) -> GoldbergConfig:
        """
        Build a GoldbergConfig from a resolved config dict.

        Used after ConfigResolver.resolve_config() to instantiate the runtime
        object from validated, default-filled values.

        Args:
            config_dict: The ``goldberg`` sub-dict returned by resolve_config().

        Returns:
            GoldbergConfig with all fields populated.
        """
        return cls(
            account_name=config_dict.get("account_name", ""),
            language=config_dict.get("language", ""),
            legacy_dlcs=config_dict.get("legacy_dlcs", False),
            unlock_all_dlcs=config_dict.get("unlock_all_dlcs", False),
            write_steam_appid=config_dict.get("write_steam_appid", True),
            preserve_user_cfg=config_dict.get("preserve_user_cfg", False),
        )  # type: ignore

    def set_account_name(self, new_account: str) -> Self:
        """Set the player account name."""
        self.account_name = new_account.strip()
        return self

    def set_language(self, new_language: str) -> Self:
        """Set the game language."""
        self.language = new_language.strip()
        return self

    def set_dlcs(self, new_dlcs: dict[str | int, str]) -> Self:
        """Set the DLC list."""
        self.dlcs = new_dlcs
        return self

    def validate(self) -> None:
        """Raise ValueError on invalid field values."""
        if not isinstance(self.account_name, str):
            raise ValueError("account_name must be a string")

        if not isinstance(self.language, str):
            raise ValueError("language must be a string")

        if self.language.lower() not in VALID_LANGUAGES:
            raise ValueError(f"language '{self.language}' is not supported")

    def _write_legacy_dlcs(self, dest: pathlib.Path) -> None:
        """Write DLCs to legacy DLC.txt — one ``appid=name`` entry per line."""
        content = "\n".join(f"{appid}={name}" for appid, name in sorted(self.dlcs.items()))
        target = dest / "DLC.txt"
        log.info("Writing %d DLC(s) to %s.", len(self.dlcs), target)
        _atomic_write_text(content, target)

    def _write_dlcs(self, dest: pathlib.Path) -> None:
        """
        Write DLCs to modern configs.app.ini format.

            [app::dlcs]
            unlock_all = 0   ; (or 1 when self.unlock_all_dlcs is True)
            12345 = DLC Name
        """
        if not self.dlcs:
            return

        target = dest / "configs.app.ini"
        app_cfg = configparser.RawConfigParser()
        app_cfg["app::dlcs"] = {
            "unlock_all": "1" if self.unlock_all_dlcs else "0",
            **{str(appid): name for appid, name in sorted(self.dlcs.items())},
        }
        log.info("Writing %d DLC(s) to %s (unlock_all=%s).", len(self.dlcs), target, self.unlock_all_dlcs)
        _atomic_write_configparser(app_cfg, target)

    def write(self, dest: pathlib.Path) -> None:
        """
        Write Goldberg configuration files to *dest* (the steam_settings directory).

        Creates:
        - ``configs.user.ini``  — account name & language
        - ``configs.app.ini``   — DLC list (modern format, default)
        - ``DLC.txt``           — DLC list (legacy format, when self.legacy_dlcs is True)

        The steam_appid.txt files are written by the emulator layer
        (``Goldberg.create_config_files``), not here, so that the placement
        logic stays in one place.

        Args:
            dest: Path to the steam_settings directory (created if absent).
        """
        if self.preserve_user_cfg and dest.exists():
            log.info("Preserving user config, skipping config...")
            return

        log.info("Writing Goldberg config to '%s'.", dest)
        dest.mkdir(parents=True, exist_ok=True)

        user_cfg = configparser.RawConfigParser()
        user_cfg["user::general"] = {
            "account_name": self.account_name,
            "language": self.language,
        }
        user_path = dest / "configs.user.ini"
        log.info("Writing %s (account_name=%r, language=%r).", user_path, self.account_name, self.language)
        _atomic_write_configparser(user_cfg, user_path)

        if self.legacy_dlcs:
            self._write_legacy_dlcs(dest)
        else:
            self._write_dlcs(dest)
