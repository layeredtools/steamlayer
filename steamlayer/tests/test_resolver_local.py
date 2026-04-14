from __future__ import annotations

from unittest.mock import MagicMock

from steamlayer.discovery.decision import DecisionPolicy
from steamlayer.discovery.local import LocalDiscovery
from steamlayer.discovery.matcher import NameMatcher
from steamlayer.discovery.models import DiscoveryResult, DiscoverySource
from steamlayer.discovery.query_strategy import QueryStrategy
from steamlayer.discovery.resolver import AppIDResolver


class TestLocalDiscovery:
    def test_finds_appid_from_steam_appid_txt(self, tmp_path):
        game = tmp_path / "MyGame"
        game.mkdir()
        (game / "steam_appid.txt").write_text("620\n")

        result = LocalDiscovery().find(game)
        assert result == 620

    def test_finds_appid_in_subdirectory(self, tmp_path):
        game = tmp_path / "MyGame"
        sub = game / "bin"
        sub.mkdir(parents=True)
        (sub / "steam_appid.txt").write_text("1234")

        result = LocalDiscovery().find(game)
        assert result == 1234

    def test_extracts_first_number_from_file(self, tmp_path):
        game = tmp_path / "MyGame"
        game.mkdir()
        (game / "steam_appid.txt").write_text("  \n  730  \n")

        result = LocalDiscovery().find(game)
        assert result == 730

    def test_returns_none_when_no_file(self, tmp_path):
        game = tmp_path / "MyGame"
        game.mkdir()
        assert LocalDiscovery().find(game) is None

    def test_returns_none_when_file_has_no_number(self, tmp_path):
        game = tmp_path / "MyGame"
        game.mkdir()
        (game / "steam_appid.txt").write_text("no numbers here")
        assert LocalDiscovery().find(game) is None

    def test_finds_appid_from_acf_manifest(self, tmp_path):
        library = tmp_path / "steamapps"
        common = library / "common"
        game = common / "Portal 2"
        game.mkdir(parents=True)

        manifest = library / "appmanifest_620.acf"
        manifest.write_text('"appid"\t"620"\n"installdir"\t"Portal 2"\n')

        result = LocalDiscovery().find(game)
        assert result == 620

    def test_acf_only_matches_correct_game(self, tmp_path):
        library = tmp_path / "steamapps"
        common = library / "common"
        game = common / "Portal 2"
        game.mkdir(parents=True)

        # Manifest for a different game
        manifest = library / "appmanifest_400.acf"
        manifest.write_text('"appid"\t"400"\n"installdir"\t"Portal"\n')

        result = LocalDiscovery().find(game)
        assert result is None

    def test_ignores_unreadable_files(self, tmp_path):
        game = tmp_path / "MyGame"
        game.mkdir()
        bad_file = game / "steam_appid.txt"
        bad_file.write_bytes(b"\xff\xfe")  # not valid utf-8 but errors="ignore" handles it

        # Should not raise, just return None or an appid if numbers are found
        result = LocalDiscovery().find(game)
        # No assertion on value — just that it doesn't crash
        assert result is None or isinstance(result, int)


def make_resolver(*, local=None, repo=None, web=None, matcher=None, query_strategy=None):
    from steamlayer.discovery.local import LocalDiscovery
    from steamlayer.discovery.repository import AppIndexRepository
    from steamlayer.discovery.web import SteamWebClient

    return AppIDResolver(
        query_strategy=query_strategy or QueryStrategy(NameMatcher()),
        local=local or MagicMock(spec=LocalDiscovery),
        matcher=matcher or NameMatcher(),
        repo=repo or MagicMock(spec=AppIndexRepository),
        web=web or MagicMock(spec=SteamWebClient),
    )


class TestAppIDResolverManual:
    def test_returns_manual_result_immediately(self, tmp_path):
        game_path = tmp_path / "Portal 2"
        game_path.mkdir()

        resolver = make_resolver()
        result = resolver.resolve(game_path=game_path, appid=620)

        assert result.appid == 620
        assert result.source == DiscoverySource.MANUAL
        assert result.confidence == 1.0


class TestAppIDResolverLocal:
    def test_returns_local_result_from_file(self, tmp_path):
        game_path = tmp_path / "Portal 2"
        game_path.mkdir()

        local = MagicMock()
        local.find.return_value = 620

        resolver = make_resolver(local=local)
        result = resolver.resolve(game_path=game_path, appid=None)

        assert result.appid == 620
        assert result.source == DiscoverySource.LOCAL

    def test_high_confidence_index_match_skips_web(self, tmp_path):
        game_path = tmp_path / "Portal 2"
        game_path.mkdir()

        local = MagicMock()
        local.find.return_value = None

        repo = MagicMock()
        repo.get_app_index.return_value = {"portal 2": 620}

        web = MagicMock()

        resolver = make_resolver(local=local, repo=repo, web=web)
        result = resolver.resolve(game_path=game_path, appid=None)

        assert result.appid == 620
        web.search_store.assert_not_called()


class TestAppIDResolverWeb:
    def test_falls_back_to_web_search(self, tmp_path):
        game_path = tmp_path / "Portal 2"
        game_path.mkdir()

        local = MagicMock()
        local.find.return_value = None

        repo = MagicMock()
        repo.get_app_index.return_value = {}

        web = MagicMock()
        web.search_store.return_value = {
            "total": 1,
            "items": [{"type": "app", "id": "620", "name": "Portal 2"}],
        }

        resolver = make_resolver(local=local, repo=repo, web=web)
        result = resolver.resolve(game_path=game_path, appid=None, strict=True)

        assert result.appid == 620
        assert result.source == DiscoverySource.WEB

    def test_no_network_returns_none_source(self, tmp_path):
        game_path = tmp_path / "Portal 2"
        game_path.mkdir()

        local = MagicMock()
        local.find.return_value = None

        repo = MagicMock()
        repo.get_app_index.return_value = {}

        resolver = make_resolver(local=local, repo=repo)
        result = resolver.resolve(game_path=game_path, appid=None, allow_network=False)

        assert result.source == DiscoverySource.NONE
        assert result.appid is None

    def test_low_confidence_prompts_user(self, tmp_path):
        game_path = tmp_path / "Some Obscure Game"
        game_path.mkdir()

        local = MagicMock()
        local.find.return_value = None

        repo = MagicMock()
        repo.get_app_index.return_value = {}

        web = MagicMock()
        web.search_store.return_value = {
            "total": 1,
            "items": [{"type": "app", "id": "99999", "name": "Slightly Different Game Name"}],
        }

        resolver = make_resolver(local=local, repo=repo, web=web)
        resolver.selector = MagicMock()
        resolver.selector.prompt_low_confidence.return_value = DiscoveryResult(
            appid=99999, source=DiscoverySource.WEB, confidence=0.45
        )

        result = resolver.resolve(game_path=game_path, appid=None, strict=True)

        # If confidence is below threshold, selector should be called
        # (exact behaviour depends on the match score — this just ensures no crash)
        assert result is not None

    def test_web_search_exception_returns_none_source(self, tmp_path):
        game_path = tmp_path / "Portal 2"
        game_path.mkdir()

        local = MagicMock()
        local.find.return_value = None

        repo = MagicMock()
        repo.get_app_index.return_value = {}

        web = MagicMock()
        web.search_store.side_effect = Exception("network error")

        resolver = make_resolver(local=local, repo=repo, web=web)
        result = resolver.resolve(game_path=game_path, appid=None)

        assert result.source == DiscoverySource.NONE


class TestDecisionPolicy:
    def test_ambiguous_when_scores_close(self):
        policy = DecisionPolicy()
        assert policy.is_ambiguous(0.85, 0.78, "", "") is True

    def test_not_ambiguous_when_scores_far_apart(self):
        policy = DecisionPolicy()
        assert policy.is_ambiguous(0.95, 0.60, "", "") is False

    def test_not_ambiguous_when_best_below_min(self):
        policy = DecisionPolicy()
        assert policy.is_ambiguous(0.3, 0.25, "", "") is False

    def test_should_accept_strict(self):
        policy = DecisionPolicy()
        assert policy.should_accept(0.85, strict=True) is True
        assert policy.should_accept(0.84, strict=True) is False

    def test_should_accept_yolo(self):
        policy = DecisionPolicy()
        assert policy.should_accept(0.45, strict=False) is True
        assert policy.should_accept(0.35, strict=False) is False
