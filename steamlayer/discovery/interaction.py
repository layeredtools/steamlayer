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

    def prompt_ambiguous_match(self, candidates: list[DiscoveryResult]) -> DiscoveryResult:
        self._io.write("\n[?] Ambiguous matches detected.")
        self._io.write("    Reason: Multiple entries are too similar to auto-select safely.\n")

        sorted_candidates = sorted(candidates, key=lambda x: x.confidence, reverse=True)
        for i, res in enumerate(sorted_candidates, start=1):
            label = f"{res.game_name} (AppID: {res.appid})"
            self._io.write(f"  {i}. {label:<50} [Conf: {res.confidence:.2f}]")

        self._io.write("  0. Enter AppID manually")
        while True:
            try:
                choice = self._prompt("\nSelect the correct game", default="1")
                idx_input = int(choice)

                if idx_input == 0:
                    manual_result = self._prompt_manual_appid()
                    if manual_result:
                        return manual_result
                    continue

                idx = idx_input - 1
                if 0 <= idx < len(sorted_candidates):
                    selected = sorted_candidates[idx]
                    selected.user_selected = True
                    return selected

            except ValueError:
                pass

            self._io.write(f"Invalid choice. Please enter 1-{len(sorted_candidates)} or 0 for manual entry.")

    def prompt_low_confidence(self, result: DiscoveryResult) -> DiscoveryResult:
        self._io.write("[!] Low confidence match found:")
        self._io.write(f"    '{result.game_name}' (AppID={result.appid}, Score={result.confidence})")
        self._io.write("    Reason: Found potential match, but score is below strict threshold (0.85).\n")

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
