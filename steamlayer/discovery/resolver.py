from __future__ import annotations

import logging
import pathlib

from .decision import DecisionPolicy
from .interaction import InteractiveSelector
from .local import LocalDiscovery
from .matcher import NameMatcher
from .models import DiscoveryResult, DiscoverySource
from .query_strategy import QueryStrategy
from .repository import AppIndexRepository
from .web import SteamWebClient

log = logging.getLogger("steamlayer.discovery.resolver")


class AppIDResolver:
    def __init__(
        self,
        *,
        query_strategy: QueryStrategy,
        local: LocalDiscovery,
        matcher: NameMatcher,
        repo: AppIndexRepository,
        web: SteamWebClient,
    ) -> None:
        self.query_strategy = query_strategy
        self.local = local
        self.matcher = matcher
        self.repo = repo
        self.web = web

        self.selector = InteractiveSelector()
        self.policy = DecisionPolicy()

    def _find_local_index(self, game_name: str) -> DiscoveryResult:
        index = self.repo.get_app_index()

        if not index:
            return DiscoveryResult(source=DiscoverySource.NONE)

        clean_query = self.matcher.clean_name(game_name).lower()
        if clean_query in index:
            return DiscoveryResult(
                appid=index[clean_query],
                source=DiscoverySource.LOCAL,
                confidence=1.0,
                game_name=clean_query,
            )

        best_match = DiscoveryResult(confidence=0.0)
        for name, appid in index.items():
            if clean_query not in name and name not in clean_query:
                continue

            conf = self.matcher.calculate_confidence(clean_query, name)
            if conf > best_match.confidence:
                best_match = DiscoveryResult(
                    appid=appid,
                    source=DiscoverySource.LOCAL,
                    confidence=conf,
                    game_name=name,
                )

            if best_match.confidence >= 1.0:
                break

        return best_match

    def _find_web(self, game_name: str) -> DiscoveryResult:
        clean_query = self.matcher.clean_name(game_name)

        if not clean_query:
            return DiscoveryResult(source=DiscoverySource.NONE)

        try:
            data = self.web.search_store(clean_query)

            if data.get("total", 0) > 0:
                candidates: list[tuple[float, dict]] = []

                for item in data["items"][:15]:
                    if item.get("type") != "app":
                        continue

                    name = item["name"]
                    score = self.matcher.calculate_confidence(clean_query, name)

                    candidates.append((score, item))

                if not candidates:
                    return DiscoveryResult(source=DiscoverySource.NONE)

                candidates.sort(key=lambda x: x[0], reverse=True)

                for score, item in candidates[:5]:
                    log.debug(f"[WEB RANK] {item['name']} -> {score}")

                best_score, best_item = candidates[0]
                second_score = candidates[1][0] if len(candidates) > 1 else 0.0

                if self.policy.is_ambiguous(best_score, second_score):
                    log.warning(
                        f"Ambiguous match detected for '{game_name}' "
                        f"(query='{clean_query}'). Switching to interactive selection."
                    )
                    return self.selector.prompt_ambiguous_match(candidates)

                log.info(f"[QUERY BEST] '{clean_query}' → {best_item['id']} '{best_item['name']}' (Conf: {best_score})")
                return DiscoveryResult(
                    appid=int(best_item["id"]),
                    source=DiscoverySource.WEB,
                    confidence=best_score,
                    game_name=best_item["name"],
                )

            return DiscoveryResult(source=DiscoverySource.NONE)

        except Exception as e:
            log.warning(f"Web search for AppID failed: {e}")
            return DiscoveryResult(source=DiscoverySource.NONE)

    def resolve(
        self,
        *,
        game_path: pathlib.Path,
        appid: int | None,
        allow_network: bool = True,
        strict: bool = True,
    ) -> DiscoveryResult:
        if appid:
            return DiscoveryResult(
                appid=appid,
                source=DiscoverySource.MANUAL,
                confidence=1.0,
            )

        local_id = self.local.find(game_path)
        if local_id:
            return DiscoveryResult(
                appid=local_id,
                source=DiscoverySource.LOCAL,
                confidence=1.0,
            )

        index_res = self._find_local_index(game_path.name)
        if index_res.confidence >= 0.9:
            log.info(f"Resolved via Local Index: {index_res.appid}")
            return index_res

        fallback_msg = "AppID discovery failed. Goldberg will use default/spacewar fallback."
        if not allow_network:
            log.info("Network disabled; skipping steam APPID lookup.")
            log.warning(fallback_msg)
            return DiscoveryResult(source=DiscoverySource.NONE)

        queries = self.query_strategy.generate(game_path.name)

        best_result: DiscoveryResult | None = None
        for query in queries:
            log.debug(f"[QUERY] Trying: '{query}'")

            res = self._find_web(query)
            if res.source == DiscoverySource.MANUAL or res.user_selected:
                return res

            if res.source != DiscoverySource.NONE:
                if best_result is None or res.confidence > best_result.confidence:
                    best_result = res

                if best_result.confidence == 1.0:
                    break

        if best_result:
            if self.policy.should_accept(best_result.confidence, strict=strict):
                log.info(
                    f"Discovered AppID {best_result.appid} '{best_result.game_name}' (Conf: {best_result.confidence})"
                )
                return best_result

            log.warning(
                f"Low confidence match: '{best_result.game_name}' "
                f"(AppID={best_result.appid}, Conf={best_result.confidence})"
            )
            return self.selector.prompt_low_confidence(best_result)

        log.warning(fallback_msg)
        return DiscoveryResult(source=DiscoverySource.NONE)
