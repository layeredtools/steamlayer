from __future__ import annotations


class DecisionPolicy:
    MIN_SCORE_FOR_AMBIGUITY = 0.5

    def is_ambiguous(
        self, best_score: float, second_score: float, target_name: str, second_candidate: str
    ) -> bool:
        if best_score < self.MIN_SCORE_FOR_AMBIGUITY:
            return False

        if (best_score - second_score) < 0.1:
            return True

        target_words = set(target_name.lower().split())
        candidate_words = set(second_candidate.lower().split())

        shared_specifics = candidate_words.intersection(target_words)
        if len(shared_specifics) > len(target_words) * 0.5:
            return True

        return False

    def should_accept(self, score: float, strict: bool) -> bool:
        threshold = 0.85 if strict else 0.4
        return score >= threshold
