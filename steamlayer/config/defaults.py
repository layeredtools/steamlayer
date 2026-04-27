from __future__ import annotations

from typing import TypedDict


class ConfigDict(TypedDict):
    steamlayer: SteamlayerConfigDict
    goldberg: GoldbergConfigDict


class SteamlayerConfigDict(TypedDict):
    strict: bool
    verbose: int
    no_network: bool
    no_defender_check: bool
    dry_run: bool
    unpack: bool


class GoldbergConfigDict(TypedDict):
    account_name: str
    language: str
    legacy_dlcs: bool
    unlock_all_dlcs: bool
    write_steam_appid: bool
    preserve_user_cfg: bool


DEFAULTS: ConfigDict = {
    "steamlayer": {
        "strict": True,
        "verbose": 0,
        "no_network": False,
        "no_defender_check": False,
        "dry_run": False,
        "unpack": False,
    },
    "goldberg": {
        # User-visible identity
        "account_name": "Player",  # string
        # Language used in configs.user.ini (must be a known value)
        "language": "english",  # string, must be in VALID_LANGUAGES
        # DLC handling
        "legacy_dlcs": False,  # bool: write DLC.txt when True, configs.app.ini when False
        "unlock_all_dlcs": False,  # bool: when True, configs.app.ini: unlock_all = 1
        # Steam ID file behaviour
        "write_steam_appid": True,  # bool: write steam_appid.txt alongside config dirs and root
        # Overwrite policy (we default to always overwrite, i.e. False = don't preserve)
        "preserve_user_cfg": False,  # bool: if True generator would attempt to keep
        # configs.user.ini (we will ignore if you want always overwrite)
        # Optional explicit DLC map (useful to persist choices in .steamlayer.toml)
    },
}

VALID_LANGUAGES = {
    "english",
    "french",
    "german",
    "spanish",
    "italian",
    "portuguese",
    "russian",
    "korean",
    "japanese",
    "chinese",
    "thai",
    "bulgarian",
    "czech",
    "danish",
    "dutch",
    "finnish",
    "greek",
    "hungarian",
    "norwegian",
    "polish",
    "romanian",
    "swedish",
    "turkish",
    "ukrainian",
    "vietnamese",
    "traditional_chinese",
    "simplified_chinese",
}


class ConfigError(Exception):
    """Raised when configuration validation fails."""

    pass
