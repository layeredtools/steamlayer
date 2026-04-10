from __future__ import annotations

import argparse
import logging
import pathlib
import time

from steamlayer import __version__
from steamlayer.bootstrap import (
    GoldbergBootstrapper,
    SevenZipBootstrapper,
    warn_about_defender_if_needed,
)
from steamlayer.discovery import DiscoveryFacade
from steamlayer.emulators.goldberg import (
    Goldberg,
    GoldbergConfig,
)
from steamlayer.game import (
    Game,
    GamePatcher,
    GameRestorer,
)
from steamlayer.http_client import HTTPClient
from steamlayer.logging_utils import configure_logging

log = logging.getLogger("steamlayer." + __name__)

TOOL_HOME = pathlib.Path.home() / ".steamlayer"
VENDORS_PATH = TOOL_HOME / "vendors"


def main():
    parser = argparse.ArgumentParser(description="SteamLayer — seamless Steam API layer replacement.")
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
        help=(
            "Enable YOLO mode: bypasses strict name matching and accepts"
            "lower-confidence AppID guesses (useful for sequels)."
        ),
    )
    parser.add_argument(
        "--cache-dir",
        type=pathlib.Path,
        default=TOOL_HOME / ".cache",
        help="Directory used for caching (e.g. DLC list). Defaults to ~/.steamlayer/.cache",
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

    args = parser.parse_args()
    if args.verbose == 0:
        level = logging.WARNING
    elif args.verbose == 1:
        level = logging.INFO
    else:
        level = logging.DEBUG
    configure_logging(level=level)

    if not args.game.exists():
        log.error(f"Game path '{args.game}' does not exist.")
        raise SystemExit(1)

    start_time = time.time()
    log.info(f"steamlayer {__version__}")

    if args.game.is_file():
        args.game = args.game.parent

    game = Game(path=args.game, appid=args.appid)
    if not args.strict:
        log.warning(
            "Running using YOLO. This could lead to wrong results. "
            "Please, double-check the result and if wrongful, restore the game using "
            "--restore and re-run supplying the --appid manually."
        )

    emulator = Goldberg(path=VENDORS_PATH / "goldberg")
    if args.restore:
        restorer = GameRestorer(game=game, emulator=emulator, dry_run=args.dry_run)
        restorer.run()
        return

    sevenzip = SevenZipBootstrapper(VENDORS_PATH / "7zip", http=None)
    goldberg = GoldbergBootstrapper(VENDORS_PATH / "goldberg", http=None)
    if args.no_network:
        log.info("Network disabled. Using existing local dependencies.")

        missing = []
        if not sevenzip.is_available():
            missing.append("7-Zip")

        if not goldberg.is_available():
            missing.append("Goldberg")

        if missing:
            log.error("Missing required components with network disabled: " + ", ".join(missing))
            raise SystemExit(1)
    else:
        try:
            if not args.no_defender_check:
                sevenzip_needed = not sevenzip.is_available()
                goldberg_needed = not goldberg.is_available()
                if sevenzip_needed or goldberg_needed:
                    warn_about_defender_if_needed(str(VENDORS_PATH))

            with HTTPClient() as http:
                SevenZipBootstrapper(VENDORS_PATH / "7zip", http).ensure()
                GoldbergBootstrapper(VENDORS_PATH / "goldberg", http).ensure()
        except RuntimeError as e:
            log.error(str(e))
            raise SystemExit(1)

    discoverer = DiscoveryFacade()
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
        game.dlcs = discoverer.fetch_dlcs(
            game.appid,
            cache_path=dlc_cache_path,
            allow_network=not args.no_network,
        )

    config = GoldbergConfig().set_dlcs(game.dlcs)
    patcher = GamePatcher(
        game=game,
        emulator=emulator,
        config=config,
        dry_run=args.dry_run,
    )
    emulator.validate()
    patcher.run()

    duration = round(time.time() - start_time, 2)
    log.debug(f"Done in: {duration}s")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.warning("Interrupted. If patching was in progress, run --restore to clean up.")
        raise SystemExit(1)
