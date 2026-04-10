from __future__ import annotations

from steamlayer.io_utils import ConsoleIO, IOInterface

from .models import DiscoveryResult, DiscoverySource


class InteractiveSelector:
    def __init__(self, io: IOInterface | None = None) -> None:
        self._io = io or ConsoleIO()

    def _prompt(self, message: str, default: str = "") -> str:
        hint = f" ({default})" if default else ""
        return self._io.read(f"{message}{hint}: ") or default

    def _prompt_manual_appid(self) -> DiscoveryResult | None:
        manual = self._prompt("Enter AppID")
        if manual.isdigit():
            return DiscoveryResult(
                appid=int(manual),
                source=DiscoverySource.MANUAL,
                confidence=1.0,
                user_selected=True,
            )
        self._io.write("Invalid AppID. Try again.")
        return None

    def prompt_ambiguous_match(self, candidates: list[tuple[float, dict]]) -> DiscoveryResult:
        self._io.write("Multiple matches found:\n")
        for i, (score, item) in enumerate(candidates[:5], start=1):
            self._io.write(f"{i}. {item['name']} (score={score})")

        self._io.write("0. Enter AppID manually")
        while True:
            try:
                choice = self._prompt("\nChoose an option", default="1")
                if choice == "0":
                    result = self._prompt_manual_appid()
                    if result:
                        return result
                    continue

                idx = int(choice) - 1
                if 0 <= idx < min(5, len(candidates)):
                    selected = candidates[idx][1]
                    return DiscoveryResult(
                        appid=int(selected["id"]),
                        source=DiscoverySource.WEB,
                        confidence=candidates[idx][0],
                        game_name=selected["name"],
                        user_selected=True,
                    )
                self._io.write("Invalid choice. Try again.")
            except (ValueError, IndexError):
                self._io.write("Invalid choice. Try again.")

    def prompt_low_confidence(self, result: DiscoveryResult) -> DiscoveryResult:
        self._io.write("Low confidence match found:")
        self._io.write(f"  '{result.game_name}' (AppID={result.appid}, Conf={result.confidence})\n")
        self._io.write("1. Proceed with this match")
        self._io.write("2. Enter AppID manually")
        self._io.write("0. Stop (use Goldberg fallback)")

        while True:
            try:
                choice = self._prompt("\nChoose an option", default="1")
                if choice == "0":
                    return DiscoveryResult(source=DiscoverySource.NONE)
                if choice == "1":
                    return result
                if choice == "2":
                    manual_result = self._prompt_manual_appid()
                    if manual_result:
                        return manual_result
                    continue
                self._io.write("Invalid choice. Try again.")
            except (ValueError, IndexError):
                self._io.write("Invalid choice. Try again.")
