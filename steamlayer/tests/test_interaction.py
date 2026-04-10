from __future__ import annotations

from steamlayer.discovery.interaction import InteractiveSelector
from steamlayer.discovery.models import DiscoveryResult, DiscoverySource


class FakeIO:
    """Scriptable IO double. Feed it responses in order; captures all output."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = iter(responses)
        self.output: list[str] = []

    def write(self, message: str) -> None:
        self.output.append(message)

    def read(self, prompt: str = "") -> str:
        return next(self._responses)


def make_candidates(names: list[str]) -> list[tuple[float, dict]]:
    return [(round(1.0 - i * 0.05, 2), {"id": str(100 + i), "name": name}) for i, name in enumerate(names)]


class TestPromptAmbiguousMatch:
    def test_user_picks_first(self):
        candidates = make_candidates(["Half-Life 2", "Half-Life 2: Deathmatch"])
        io = FakeIO(responses=["1"])
        result = InteractiveSelector(io=io).prompt_ambiguous_match(candidates)

        assert result.appid == 100
        assert result.game_name == "Half-Life 2"
        assert result.user_selected is True
        assert result.source == DiscoverySource.WEB

    def test_user_picks_second(self):
        candidates = make_candidates(["Half-Life 2", "Half-Life 2: Deathmatch"])
        io = FakeIO(responses=["2"])
        result = InteractiveSelector(io=io).prompt_ambiguous_match(candidates)

        assert result.appid == 101
        assert result.game_name == "Half-Life 2: Deathmatch"

    def test_invalid_then_valid(self):
        candidates = make_candidates(["Portal", "Portal 2"])
        io = FakeIO(responses=["99", "1"])  # out-of-range first, then valid
        result = InteractiveSelector(io=io).prompt_ambiguous_match(candidates)

        assert result.appid == 100
        assert "Invalid choice" in "\n".join(io.output)

    def test_non_numeric_then_valid(self):
        candidates = make_candidates(["Portal", "Portal 2"])
        io = FakeIO(responses=["abc", "2"])
        result = InteractiveSelector(io=io).prompt_ambiguous_match(candidates)

        assert result.appid == 101

    def test_manual_appid_entry(self):
        candidates = make_candidates(["Portal", "Portal 2"])
        io = FakeIO(responses=["0", "420"])  # choose manual, then type appid
        result = InteractiveSelector(io=io).prompt_ambiguous_match(candidates)

        assert result.appid == 420
        assert result.source == DiscoverySource.MANUAL
        assert result.user_selected is True

    def test_manual_invalid_then_valid_appid(self):
        candidates = make_candidates(["Portal", "Portal 2"])
        io = FakeIO(responses=["0", "notanumber", "0", "999"])
        result = InteractiveSelector(io=io).prompt_ambiguous_match(candidates)

        assert result.appid == 999
        assert result.source == DiscoverySource.MANUAL


class TestPromptLowConfidence:
    def _low_conf_result(self) -> DiscoveryResult:
        return DiscoveryResult(
            appid=12345,
            source=DiscoverySource.WEB,
            confidence=0.45,
            game_name="Cyberpunk 2078",
        )

    def test_user_accepts(self):
        io = FakeIO(responses=["1"])
        result = InteractiveSelector(io=io).prompt_low_confidence(self._low_conf_result())

        assert result.appid == 12345
        assert result.source == DiscoverySource.WEB

    def test_user_stops(self):
        io = FakeIO(responses=["0"])
        result = InteractiveSelector(io=io).prompt_low_confidence(self._low_conf_result())

        assert result.source == DiscoverySource.NONE
        assert result.appid is None

    def test_user_enters_manual_appid(self):
        io = FakeIO(responses=["2", "77777"])
        result = InteractiveSelector(io=io).prompt_low_confidence(self._low_conf_result())

        assert result.appid == 77777
        assert result.source == DiscoverySource.MANUAL

    def test_invalid_then_accept(self):
        io = FakeIO(responses=["9", "1"])
        result = InteractiveSelector(io=io).prompt_low_confidence(self._low_conf_result())

        assert result.appid == 12345
        assert "Invalid choice" in "\n".join(io.output)

    def test_manual_invalid_appid_then_accept(self):
        """Bad manual input should re-prompt, not crash."""
        io = FakeIO(responses=["2", "notanumber", "1"])
        result = InteractiveSelector(io=io).prompt_low_confidence(self._low_conf_result())

        assert result.appid == 12345
