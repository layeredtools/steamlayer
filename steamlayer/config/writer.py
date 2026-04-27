from __future__ import annotations

import logging
import pathlib
from datetime import datetime
from typing import TYPE_CHECKING

import tomli_w

from steamlayer import __version__

if TYPE_CHECKING:
    from steamlayer.emulators import EmulatorConfig

log = logging.getLogger("steamlayer.config.writer")


def _atomic_write_toml(payload: dict, dest: pathlib.Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".tmp")
    with open(tmp, "wb") as f:
        tomli_w.dump(payload, f, indent=2)

    tmp.replace(dest)


def _build_game_config_payload(
    *,
    appid: int | None,
    config: EmulatorConfig,
    dlcs: dict[str | int, str],
    unpack: bool,
    config_created: bool,
) -> dict:
    return {
        "appid": appid,
        "goldberg": {
            "account_name": getattr(config, "account_name", None),
            "language": getattr(config, "language", None),
        },
        "dlcs": {str(k): v for k, v in dlcs.items()},
        "patch": {
            "unpack": unpack,
            "config_created": config_created,
        },
        "meta": {
            "created_by": "steamlayer",
            "steamlayer_version": __version__,
            "created_at": datetime.utcnow().isoformat() + "Z",
        },
    }


def write_game_config(
    game_path: pathlib.Path,
    *,
    appid: int | None,
    config: EmulatorConfig,
    dlcs: dict[str | int, str],
    unpack: bool,
    config_created: bool,
) -> None:
    """
    Write `.steamlayer.toml` to game_path.

    Owns the payload structure entirely — callers pass typed args,
    not raw dicts. This is the single place that knows what goes
    into the file and in what shape.
    """
    payload = _build_game_config_payload(
        appid=appid,
        config=config,
        dlcs=dlcs,
        unpack=unpack,
        config_created=config_created,
    )
    dest = game_path / ".steamlayer.toml"
    _atomic_write_toml(payload, dest)
    log.info(f"Wrote .steamlayer.toml to '{game_path}'.")
