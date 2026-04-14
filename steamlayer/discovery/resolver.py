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
        for raw_name, appid in index.items():
            clean_index_name = self.matcher.clean_name(raw_name, is_folder=False)
            if clean_query not in clean_index_name and clean_index_name not in clean_query:
                continue

            conf = self.matcher.calculate_confidence(clean_query, clean_index_name)
            if conf > best_match.confidence:
                best_match = DiscoveryResult(
                    appid=appid,
                    source=DiscoverySource.LOCAL,
                    confidence=conf,
                    game_name=clean_query,
                )

            if best_match.confidence >= 1.0:
                break

        return best_match

    def _find_web(self, query: str) -> list[DiscoveryResult]:
        if not query:
            return []

        try:
            data = self.web.search_store(query)
            if data.get("total", 0) <= 0:
                return []

            candidates: list[tuple[float, dict]] = []
            for item in data["items"][:15]:
                if item.get("type") != "app":
                    continue

                name = item["name"]
                score = self.matcher.calculate_confidence(query, name)
                for sep in (":", " - "):
                    if sep in name:
                        parts = name.split(sep, 1)
                        base_score = self.matcher.calculate_confidence(query, parts[0].strip())
                        score = max(score, base_score - 0.01)
                        if len(parts) > 1:
                            sub_score = self.matcher.calculate_confidence(query, parts[1].strip())
                            score = max(score, sub_score - 0.01)  # could be DLC subtitle
                candidates.append((score, item))

            if not candidates:
                return []

            results = []
            candidates.sort(key=lambda x: x[0], reverse=True)
            for score, item in candidates[:9]:
                results.append(
                    DiscoveryResult(
                        appid=int(item["id"]),
                        source=DiscoverySource.WEB,
                        confidence=score,
                        game_name=item["name"],
                    )
                )
            return results

        except Exception as e:
            log.warning(f"Web search for AppID failed: {e}")
            return []

    def resolve(
        self,
        *,
        game_path: pathlib.Path,
        appid: int | None,
        allow_network: bool = True,
        strict: bool = True,
    ) -> DiscoveryResult:
        if appid is not None:
            return DiscoveryResult(
                appid=appid,
                source=DiscoverySource.MANUAL,
                confidence=1.0,
            )

        original_name = game_path.name
        local_id = self.local.find(game_path)
        if local_id:
            return DiscoveryResult(appid=local_id, source=DiscoverySource.LOCAL, confidence=1.0)

        index_res = self._find_local_index(original_name)
        all_candidates: list[DiscoveryResult] = []
        if index_res.appid is not None:
            if index_res.confidence >= 0.85:
                log.info(f"Resolved via local index: {index_res.appid}")
                return index_res

            elif index_res.confidence > 0.4:
                all_candidates.append(index_res)

        if not allow_network:
            log.warning("AppID discovery failed. Network is disabled.")
            return DiscoveryResult(source=DiscoverySource.NONE)

        log.info(f"Searching Steam for: '{original_name}'...")
        queries = self.query_strategy.generate(original_name)
        for query in queries:
            log.debug(f"[QUERY] Trying: '{query}'")
            web_results = self._find_web(query)

            for res in web_results:
                res.confidence = self.matcher.calculate_confidence(original_name, res.game_name or "")
                if res.confidence > 0.4:
                    all_candidates.append(res)

            if any(c.confidence >= 1.0 for c in all_candidates):
                break

        if all_candidates:
            all_candidates.sort(key=lambda x: x.confidence, reverse=True)
            seen_ids = set()
            unique_candidates = []
            for c in all_candidates:
                if c.appid not in seen_ids:
                    unique_candidates.append(c)
                    seen_ids.add(c.appid)

            best = unique_candidates[0]
            if len(unique_candidates) > 1:
                second = unique_candidates[1]

                is_ambiguous = self.policy.is_ambiguous(
                    best_score=best.confidence,
                    second_score=second.confidence,
                    target_name=original_name,
                    second_candidate=second.game_name or "",
                )

                if is_ambiguous and best.confidence < 1.0:
                    log.info(f"Multiple close matches found for '{original_name}'.")
                    return self.selector.prompt_ambiguous_match(unique_candidates[:9])

            if self.policy.should_accept(best.confidence, strict=strict):
                log.info(f"Discovered AppID {best.appid} '{best.game_name}' (Conf: {best.confidence})")
                return best

            return self.selector.prompt_low_confidence(best)

        log.warning("AppID discovery failed.")
        return DiscoveryResult(source=DiscoverySource.NONE)
