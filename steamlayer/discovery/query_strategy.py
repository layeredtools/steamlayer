from __future__ import annotations

import re


class QueryStrategy:
    """
    Strategy:
    1. Try full name (with modifiers)
    2. Remove modifiers (replacement)
    3. Remove irrelevant words
    4. Remove captions
    5. Progressively simplify
    """

    MODIFIERS = {
        "remake",
        "remastered",
        "goty",
        "edition",
        "complete",
        "bundle",
    }

    STOPWORDS = {"the", "a", "an"}

    def _normalize(self, name: str) -> str:
        name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
        name = name.lower()
        name = re.sub(r"[^a-z0-9\s:]", "", name)
        name = " ".join(name.split())
        return name.strip()

    def _remove_stopwords(self, name: str) -> str:
        words = name.split()
        filtered = [w for w in words if w not in self.STOPWORDS]
        return " ".join(filtered)

    def _remove_modifiers(self, name: str) -> str:
        words = name.split()
        filtered = [w for w in words if w not in self.MODIFIERS]
        return " ".join(filtered)

    def generate(self, name: str) -> list[str]:
        queries: list[str] = []

        base = self._normalize(name)
        words = base.split()

        queries.append(base)

        no_modifiers = self._remove_modifiers(base)
        if no_modifiers and no_modifiers != base:
            queries.append(no_modifiers)

        no_stop = self._remove_stopwords(no_modifiers)
        if no_stop and no_stop != no_modifiers:
            queries.append(no_stop)

        if ":" in base:
            main = base.split(":")[0].strip()
            if main:
                queries.append(main)

        if len(words) >= 2:
            queries.append(" ".join(words[:2]))

        if words:
            queries.append(words[0])

        no_numbers = re.sub(r"\b\d+\b", "", no_modifiers).strip()
        if no_numbers and no_numbers != no_modifiers:
            no_numbers = " ".join(no_numbers.split())
            if no_numbers:
                queries.append(no_numbers)

        seen = set()
        result = []
        for q in queries:
            if q and q not in seen:
                result.append(q)
                seen.add(q)

        return result
