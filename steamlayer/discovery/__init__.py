from __future__ import annotations

import pathlib

from steamlayer.http_client import HTTPClient

from .dlc import DLCService
from .local import LocalDiscovery
from .matcher import NameMatcher
from .query_strategy import QueryStrategy
from .repository import AppIndexRepository
from .resolver import AppIDResolver
from .web import SteamWebClient


class DiscoveryFacade:
    def __init__(
        self,
        http: HTTPClient,
        data_dir: pathlib.Path | None = None,
        *,
        allow_network: bool = True,
    ):
        repo = AppIndexRepository(data_dir=data_dir, http=http, allow_network=allow_network)
        web = SteamWebClient(http=http)

        self.resolver = AppIDResolver(
            query_strategy=QueryStrategy(),
            local=LocalDiscovery(),
            matcher=NameMatcher(),
            repo=repo,
            web=web,
        )
        self.dlc = DLCService(
            repo=repo,
            web=web,
        )

    def try_resolve_id_for_game(self, **kwargs):
        return self.resolver.resolve(**kwargs)

    def fetch_dlcs(self, *args, **kwargs):
        return self.dlc.fetch(*args, **kwargs)
