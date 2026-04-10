from __future__ import annotations

import re
from difflib import SequenceMatcher


class NameMatcher:
    SCENE_PATTERNS = [
        r"v\d+(\.\d+)*",
        r"\d+\.\d+(\.\d+)*",
        r"repack",
        r"dodi",
        r"fitgirl",
        r"elamigos",
        r"build\.\d+",
        r"goldberg",
        r"crack",
        r"multi\d+",
    ]

    BAD_TOKENS = {
        "soundtrack",
        "demo",
        "dlc",
        "beta",
        "test",
        "editor",
        "sdk",
        "tool",
        "kit",
    }

    def clean_name(self, name: str) -> str:
        for pattern in self.SCENE_PATTERNS:
            name = re.sub(pattern, "", name, flags=re.IGNORECASE)

        name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
        name = name.replace(".", " ").replace("_", " ")

        return " ".join(name.split()).strip()

    def calculate_confidence(self, target: str, candidate: str) -> float:
        clean_local = self.clean_name(target).lower()
        clean_steam = self.clean_name(candidate).lower()

        t = re.sub(r"[^a-z0-9]", "", clean_local)
        c = re.sub(r"[^a-z0-9]", "", clean_steam)

        if not t or not c:
            return 0.0

        if t == c:
            return 1.0

        ratio = SequenceMatcher(None, t, c).ratio()

        tokens_t = set(clean_local.split())
        tokens_c = set(clean_steam.split())

        if tokens_t & tokens_c:
            ratio = max(ratio, 0.75)

        numbers_t = re.findall(r"\d+", clean_local)
        numbers_c = re.findall(r"\d+", clean_steam)
        if numbers_t and numbers_t == numbers_c:
            ratio += 0.05

        if ":" in clean_steam:
            ratio += 0.08

        if tokens_t.issubset(tokens_c) or tokens_c.issubset(tokens_t):
            ratio = max(ratio, 0.8)

        extra_tokens = tokens_c - tokens_t
        bad_extras = extra_tokens & self.BAD_TOKENS
        if bad_extras:
            ratio -= 0.2 * len(bad_extras)

        if extra_tokens:
            ratio -= 0.02 * len(extra_tokens)

        if t != c:
            length_diff = abs(len(t) - len(c))
            ratio -= 0.02 * length_diff

        return round(max(0.0, min(1.0, ratio)), 2)
