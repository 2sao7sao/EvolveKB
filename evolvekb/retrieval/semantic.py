from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from evolvekb.retrieval.base import EvidenceItem, EvidencePack, build_citations
from evolvekb.retrieval.keyword import build_lexical_corpus, tokenize_terms


class SemanticRetriever:
    name = "semantic"

    def retrieve(
        self,
        repo: Path,
        query: str,
        *,
        intent: str | None = None,
        limit: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> EvidencePack:
        query_vector = _semantic_vector(query)
        corpus = build_lexical_corpus(repo)
        scored_items: list[EvidenceItem] = []
        if query_vector:
            for item in corpus:
                text = str(item.metadata.get("haystack") or item.text)
                score = _cosine(query_vector, _semantic_vector(text))
                if score > 0:
                    scored_items.append(item.model_copy(update={"score": score, "retrieval_mode": self.name}))
        items = sorted(scored_items, key=lambda item: (-item.score, item.asset_type, item.name))[:limit]
        missing = [] if items else [f"No semantic-lite evidence found for query: {query}"]
        return EvidencePack(
            query=query,
            intent=intent,
            retrieval_modes=[self.name],
            items=items,
            citations=build_citations(items),
            missing_evidence=missing,
            retrieval_trace={
                "retriever": self.name,
                "candidate_count": len(corpus),
                "matched_count": len(scored_items),
                "limit": limit,
                "scoring_formula": "cosine over deterministic token and character-ngram features",
                "external_dependencies": [],
                "filters": filters or {},
            },
            confidence=max((item.score for item in items), default=None),
        )


def _semantic_vector(text: str) -> dict[str, float]:
    features: dict[str, float] = {}
    for token in tokenize_terms(text):
        features[f"tok:{token}"] = features.get(f"tok:{token}", 0.0) + 1.0
        padded = f"_{token}_"
        for idx in range(max(0, len(padded) - 2)):
            gram = padded[idx : idx + 3]
            features[f"tri:{gram}"] = features.get(f"tri:{gram}", 0.0) + 0.25
    return features


def _cosine(left: dict[str, float], right: dict[str, float]) -> float:
    if not left or not right:
        return 0.0
    dot = sum(value * right.get(key, 0.0) for key, value in left.items())
    if dot <= 0:
        return 0.0
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    return dot / max(left_norm * right_norm, 1e-9)
