from __future__ import annotations

import configparser
import logging
import pathlib
from dataclasses import dataclass, field
from typing import Self

from steamlayer.emulators import EmulatorConfig

log = logging.getLogger("steamlayer." + __name__)


@dataclass
class GoldbergConfig(EmulatorConfig):
    account_name: str = "Player"
    language: str = "english"
    dlcs: dict[int, str] = field(default_factory=dict)

    def _sanitize_string(self, string: str) -> str:
        return string.strip()

    def _write_legacy_dlcs(self, dest: pathlib.Path) -> None:
        content = "\n".join([f"{appid}={name}" for appid, name in sorted(self.dlcs.items())])
        (dest / "DLC.txt").write_text(content, encoding="utf-8")
        log.info(f"Written DLC.txt with {len(self.dlcs)} DLC entries.")

    def _write_dlcs(self, dest: pathlib.Path) -> None:
        dlcs = self.dlcs
        if dlcs:
            app_cfg = configparser.RawConfigParser()
            app_cfg["app::dlcs"] = {
                "unlock_all": "0",
                **{str(appid): name for appid, name in sorted(dlcs.items())},
            }
            with open(dest / "configs.app.ini", "w", encoding="utf-8") as f:
                app_cfg.write(f)
            log.info(f"Written configs.app.ini with {len(dlcs)} DLC entries.")

    def set_account_name(self, new_account: str) -> Self:
        self.account_name = self._sanitize_string(new_account)
        return self

    def set_language(self, new_language: str) -> Self:
        self.language = self._sanitize_string(new_language)
        return self

    def set_dlcs(self, new_dlcs: dict[int, str]) -> Self:
        self.dlcs = new_dlcs
        return self

    def write(self, dest: pathlib.Path, *, legacy_dlcs: bool = False) -> None:
        """'dest' should be the path to the 'steam_settings' directory."""

        log.info(f"Writing Goldberg config to '{dest}'...")
        dest.mkdir(parents=True, exist_ok=True)

        user_cfg = configparser.RawConfigParser()
        user_cfg["user::general"] = {
            "account_name": self.account_name,
            "language": self.language,
        }

        user_path = dest / "configs.user.ini"
        if not user_path.exists():
            with open(user_path, "w", encoding="utf-8") as f:
                user_cfg.write(f)
            log.info(f"Written configs.user.ini (account_name='{self.account_name}', language='{self.language}').")
        else:
            log.info("configs.user.ini already exists — skipping to preserve user preferences.")

        if legacy_dlcs:
            log.info("Using legacy DLC configuration.")
            return self._write_legacy_dlcs(dest)
        return self._write_dlcs(dest)
