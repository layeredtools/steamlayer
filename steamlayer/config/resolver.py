from __future__ import annotations

import logging
import pathlib
import tomllib
from typing import Any, cast

from steamlayer import TOOL_HOME

from .defaults import DEFAULTS, VALID_LANGUAGES, ConfigError

log = logging.getLogger("steamlayer.config.resolver")


class ConfigResolver:
    def __init__(self, game_dir: pathlib.Path | None = None) -> None:
        self._game_dir = game_dir
        self._global_config = self._load_toml(TOOL_HOME / "config.toml")
        self._game_config = self._load_toml(self._game_dir / ".steamlayer.toml") if self._game_dir else {}
        self._merged_config = self.deep_merge(self._global_config, self._game_config)
        self.validate(self._merged_config)

    def _load_toml(self, path: pathlib.Path | None) -> dict[str, Any]:
        if not path or not path.exists():
            return {}
        try:
            with open(path, "rb") as f:
                return tomllib.load(f)
        except Exception as e:
            log.warning(f"Could not load config from '{path}': {e}")
            return {}

    def deep_merge(self, base: dict, override: dict) -> dict:
        """
        Recursively merge override into base, respecting section boundaries.

        Each top-level section ([steamlayer], [goldberg], etc.) is merged
        independently — a missing [goldberg] in override doesn't erase base [goldberg].
        """
        result = {k: v.copy() if isinstance(v, dict) else v for k, v in base.items()}
        for key, val in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(val, dict):
                result[key].update(val)
            else:
                result[key] = val
        return result

    def validate(self, cfg: dict) -> None:
        """
        Validate configuration structure and values.

        Raises ConfigError if:
        - Unknown keys present in [steamlayer] or [goldberg]
        - Type mismatch for any known key
        - Unrecognised language value in [goldberg]
        """
        steamlayer_cfg = cfg.get("steamlayer", {})
        goldberg_cfg = cfg.get("goldberg", {})
        sl_defaults: dict[str, Any] = cast(dict[str, Any], DEFAULTS["steamlayer"])
        gb_defaults: dict[str, Any] = cast(dict[str, Any], DEFAULTS["goldberg"])

        valid_sl_keys = set(sl_defaults.keys())
        unknown_sl = set(steamlayer_cfg.keys()) - valid_sl_keys
        if unknown_sl:
            raise ConfigError(f"Unknown keys in [steamlayer]: {unknown_sl}")

        for key, val in steamlayer_cfg.items():
            expected_type = type(sl_defaults[key])
            if not isinstance(val, expected_type):
                raise ConfigError(
                    f"[steamlayer] {key}: expected {expected_type.__name__}, got {type(val).__name__}"
                )

        valid_gb_keys = set(gb_defaults.keys())
        unknown_gb = set(goldberg_cfg.keys()) - valid_gb_keys
        if unknown_gb:
            raise ConfigError(f"Unknown keys in [goldberg]: {unknown_gb}")

        for key, val in goldberg_cfg.items():
            if key == "dlcs":
                continue

            expected_type = type(gb_defaults[key])
            if not isinstance(val, expected_type):
                raise ConfigError(f"[goldberg] {key}: expected {expected_type.__name__}, got {type(val).__name__}")

        language = goldberg_cfg.get("language", gb_defaults["language"])
        if language.lower() not in VALID_LANGUAGES:
            raise ConfigError(
                f"[goldberg] language '{language}' not recognized. "
                f"Valid options: {', '.join(sorted(VALID_LANGUAGES))}"
            )

        log.debug("Configuration validation passed.")

    def resolve_config(self) -> dict[str, Any]:
        """
        Return the fully-resolved config: DEFAULTS < global config < game config.

        1. Start from DEFAULTS for every known section.
        2. Overlay the already-merged (global + game) config on top.
        3. Return.

        The result is guaranteed to contain every key in DEFAULTS, which means
        callers can safely do cfg["steamlayer"]["dry_run"] without KeyError even
        if the user's config file is empty or absent.

        Validation was already performed during __init__; a ConfigError raised
        there will have prevented construction, so by the time this method is
        called the config is known-good.
        """
        result: dict[str, Any] = {}
        flat_defaults = cast(dict[str, dict[str, Any]], DEFAULTS)
        for section, section_defaults in flat_defaults.items():
            result[section] = dict(section_defaults)
            merged_section = self._merged_config.get(section, {})
            result[section].update(merged_section)

        log.debug("Resolved config: %s", result)
        return result
