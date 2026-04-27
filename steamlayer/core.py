"""Main entry point and orchestration."""

from __future__ import annotations

import argparse
import logging
import pathlib
import time

from steamlayer import TOOL_HOME, VENDORS_PATH, __version__
from steamlayer.bootstrap import (
    GoldbergBootstrapper,
    SevenZipBootstrapper,
    SteamlessBootstrapper,
    warn_about_defender_if_needed,
)
from steamlayer.config import ConfigError, ConfigResolver
from steamlayer.discovery import DiscoveryFacade
from steamlayer.emulators.goldberg import Goldberg, GoldbergConfig
from steamlayer.game import Game, GamePatcher, GameRestorer
from steamlayer.http_client import HTTPClient
from steamlayer.logging_utils import configure_logging, spinner, success

log = logging.getLogger("steamlayer.core")


def _bootstrap_args() -> argparse.Namespace:
    """
    Two-pass argument parsing:
    1. Extract `game` positional argument (unknown args allowed)
    2. Resolve config hierarchy
    3. Re-parse with config as defaults
    """
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("game", type=pathlib.Path, nargs="?", default=None)
    pre_args, _ = pre.parse_known_args()

    resolver = ConfigResolver(game_dir=pre_args.game)
    try:
        cfg = resolver.resolve_config()
    except ConfigError as e:
        log.error(f"Configuration error: {e}")
        raise SystemExit(1)

    parser = _build_parser()
    parser.set_defaults(**cfg["steamlayer"])
    return parser.parse_args()


def _build_parser() -> argparse.ArgumentParser:
    """Build the complete argument parser."""
    parser = argparse.ArgumentParser(description="steamlayer — seamless Steam API layer replacement.")
    parser.add_argument("game", type=pathlib.Path, help="Path to the game directory.")
    parser.add_argument("-a", "--appid", type=int, default=None, help="Steam App ID of the game.")
    parser.add_argument("-d", "--dry-run", action="store_true", help="Perform a trial run with no changes made.")
    parser.add_argument(
        "-n",
        "--no-network",
        action="store_true",
        help="Disable all network access (use cached data only).",
    )
    parser.add_argument("-r", "--restore", action="store_true", help="Undo patches and restore original files.")
    parser.add_argument(
        "--version",
        action="version",
        version=f"steamlayer {__version__}",
        help="Show the installed version and exit.",
    )
    parser.add_argument(
        "-y",
        "--yolo",
        action="store_false",
        dest="strict",
        help="Enable YOLO mode: bypasses strict name matching.",
    )
    parser.add_argument(
        "--cache-dir",
        type=pathlib.Path,
        default=TOOL_HOME / ".cache",
        help="Directory used for caching.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (-v = info, -vv = debug).",
    )
    parser.add_argument(
        "--no-defender-check",
        action="store_true",
        help="Skip the Windows Defender real-time protection warning.",
    )
    parser.add_argument(
        "-u",
        "--unpack",
        action="store_true",
        help="Automatically run Steamless to unpack executables with SteamStub DRM.",
    )

    return parser


def _check_missing_vendors(*, args: argparse.Namespace) -> list[str]:
    """Check which vendors are missing (without network access)."""
    steamless = SteamlessBootstrapper(VENDORS_PATH / "steamless", http=None)
    sevenzip = SevenZipBootstrapper(VENDORS_PATH / "7zip", http=None)
    goldberg = GoldbergBootstrapper(VENDORS_PATH / "goldberg", http=None)

    missing = []
    if not sevenzip.is_available():
        missing.append("7-Zip")
    if not goldberg.is_available():
        missing.append("Goldberg")
    if args.unpack and not steamless.is_available():
        missing.append("Steamless")

    return missing


def _run_discovery_and_patch(
    args: argparse.Namespace,
    game: Game,
    emulator: Goldberg,
    discoverer: DiscoveryFacade,
    resolved_cfg: dict,
) -> None:
    """Run AppID discovery and patch the game."""
    if args.appid is None:
        log.info("No AppID provided. Attempting automatic detection...")
        result = discoverer.try_resolve_id_for_game(
            game_path=game.path,
            appid=game.appid,
            allow_network=not args.no_network,
            strict=args.strict,
        )
        game.appid = result.appid

    if game.appid is not None:
        dlc_cache_path = args.cache_dir / f"dlcs_{game.appid}.json"
        with spinner("Fetching DLC metadata..."):
            game.dlcs = discoverer.fetch_dlcs(
                game.appid,
                cache_path=dlc_cache_path,
                allow_network=not args.no_network,
            )

    config = GoldbergConfig.from_config(resolved_cfg["goldberg"]).set_dlcs(game.dlcs)
    patcher = GamePatcher(
        game=game,
        emulator=emulator,
        config=config,
        dry_run=args.dry_run,
        unpack=args.unpack,
    )

    emulator.validate()
    patcher.run()


def main() -> None:
    """Main entry point."""
    try:
        args = _bootstrap_args()
    except ConfigError as e:
        log.error(f"Failed to bootstrap arguments: {e}")
        raise SystemExit(1)

    if args.verbose == 0:
        level = logging.WARNING
    elif args.verbose == 1:
        level = logging.INFO
    else:
        level = logging.DEBUG
    configure_logging(level=level)

    log.info(f"steamlayer {__version__}")

    if not args.game.exists():
        log.error(f"Game path '{args.game}' does not exist.")
        raise SystemExit(1)

    if args.game.is_file():
        args.game = args.game.parent

    start_time = time.time()

    game = Game(path=args.game, appid=args.appid)
    if not args.strict:
        log.warning(
            "Running using YOLO. This could lead to wrong results. "
            "Please double-check and use --restore + --appid if needed."
        )

    emulator = Goldberg(path=VENDORS_PATH / "goldberg")
    if args.restore:
        with spinner("Restoring the patch..."):
            restorer = GameRestorer(game=game, emulator=emulator, dry_run=args.dry_run)
            restorer.run()
            if not args.dry_run:
                success(f"Restored '{game.path.name}' successfully.")
        return

    if args.no_network:
        missing = _check_missing_vendors(args=args)
        if missing:
            log.error("The following dependencies are missing and cannot be downloaded in offline mode:")
            for item in missing:
                log.error(f" - {item}")
            raise SystemExit(1)

    with HTTPClient() as http:
        try:
            if not args.no_defender_check:
                with spinner("Checking if real-time protection is on..."):
                    warn_about_defender_if_needed(str(VENDORS_PATH))

            if args.unpack:
                with spinner("Bootstrapping Steamless..."):
                    SteamlessBootstrapper(VENDORS_PATH / "steamless", http=http).ensure(
                        allow_network=not args.no_network
                    )

            with spinner("Bootstrapping 7-Zip..."):
                SevenZipBootstrapper(VENDORS_PATH / "7zip", http).ensure(allow_network=not args.no_network)

            with spinner("Bootstrapping Goldberg..."):
                GoldbergBootstrapper(VENDORS_PATH / "goldberg", http).ensure(allow_network=not args.no_network)

        except RuntimeError as e:
            log.error(str(e))
            raise SystemExit(1)

        try:
            resolver = ConfigResolver(game_dir=args.game)
            resolved_cfg = resolver.resolve_config()
        except ConfigError as e:
            log.error(f"Configuration error during patching: {e}")
            raise SystemExit(1)

        discoverer = DiscoveryFacade(http=http, allow_network=not args.no_network)
        _run_discovery_and_patch(args, game, emulator, discoverer, resolved_cfg)

    dlc_count = len(game.dlcs)
    success(
        f"{'[DRY RUN] ' if args.dry_run else ''}Patched '{game.path.name}' "
        f"(AppID {game.appid}, {dlc_count} DLC{'s' if dlc_count != 1 else ''})"
    )

    duration = round(time.time() - start_time, 2)
    log.debug(f"Done in: {duration}s")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.warning("Interrupted. If patching was in progress, run --restore to clean up.")
        raise SystemExit(1)
