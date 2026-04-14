from unittest.mock import MagicMock

import pytest

from steamlayer.discovery.dlc import DLCService
from steamlayer.discovery.matcher import NameMatcher
from steamlayer.discovery.repository import AppIndexRepository
from steamlayer.discovery.web import SteamWebClient


@pytest.fixture
def matcher():
    return NameMatcher()


@pytest.fixture
def dlc_service():
    repo = MagicMock(spec=AppIndexRepository)
    web = MagicMock(spec=SteamWebClient)
    return DLCService(repo=repo, web=web)


def test_clean_name_splitting(matcher: NameMatcher):
    assert matcher.clean_name("YuppiePsycho") == "yuppie psycho"
    assert matcher.clean_name("Portal.v1.0.REPACK") == "portal"


def test_calculate_confidence_sequel_penalty(matcher: NameMatcher):
    score_perfect = matcher.calculate_confidence("Portal", "Portal")
    score_sequel = matcher.calculate_confidence("Portal", "Portal 2")

    assert score_perfect == 1.0
    assert score_sequel <= 0.92
    assert score_perfect > score_sequel


def test_substring_bonus_executive_edition(matcher: NameMatcher):
    score = matcher.calculate_confidence("Yuppie Psycho", "Yuppie Psycho: Executive Edition")
    assert 0.65 <= score


def test_fetch_dlcs_failure_handling(dlc_service: DLCService):
    dlc_service.web.get_app_details = MagicMock(side_effect=Exception("Steam is down"))
    dlc_service.repo.get_dlc_index = MagicMock(return_value={})

    dlcs = dlc_service.fetch(12345, allow_network=True)
    assert dlcs == {}


def test_fetch_dlcs_individual_failure(dlc_service: DLCService):
    dlc_service.web.get_app_details = MagicMock(
        side_effect=[
            {"12345": {"success": True, "data": {"dlc": [111, 222]}}},
            Exception("Steam is down"),
            {"222": {"success": True, "data": {"name": "Some DLC"}}},
        ]
    )

    dlc_service.repo.get_dlc_index = MagicMock(return_value={})
    dlcs = dlc_service.fetch(12345, allow_network=True)

    assert dlcs[111] == "DLC 111"  # fallback
    assert dlcs[222] == "Some DLC"  # resolved correctly
