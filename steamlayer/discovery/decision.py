from __future__ import annotations


class DecisionPolicy:
    MIN_SCORE_FOR_AMBIGUITY = 0.5

    def is_ambiguous(self, best_score: float, second_score: float) -> bool:
        if best_score < self.MIN_SCORE_FOR_AMBIGUITY:
            return False
        return (best_score - second_score) < 0.1

    def should_accept(self, score: float, strict: bool) -> bool:
        threshold = 0.6 if strict else 0.4
        return score >= threshold
