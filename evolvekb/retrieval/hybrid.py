from __future__ import annotations

from pathlib import Path
from typing import Any

from evolvekb.retrieval.base import EvidenceItem, EvidencePack, build_citations
from evolvekb.retrieval.bm25 import BM25Retriever
from evolvekb.retrieval.keyword import KeywordRetriever
from evolvekb.retrieval.registry import register_retriever
from evolvekb.retrieval.semantic import SemanticRetriever


@register_retriever("hybrid")
class HybridRetriever:
    name = "hybrid"

    def __init__(
        self,
        *,
        keyword_weight: float = 0.35,
        bm25_weight: float = 0.35,
        semantic_weight: float = 0.2,
        evidence_weight: float = 0.1,
    ):
        self.keyword_weight = keyword_weight
        self.bm25_weight = bm25_weight
        self.semantic_weight = semantic_weight
        self.evidence_weight = evidence_weight

    def retrieve(
        self,
        repo: Path,
        query: str,
        *,
        intent: str | None = None,
        limit: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> EvidencePack:
        keyword_pack = KeywordRetriever().retrieve(repo, query, intent=intent, limit=limit, filters=filters)
        bm25_pack = BM25Retriever().retrieve(repo, query, intent=intent, limit=limit, filters=filters)
        semantic_pack = SemanticRetriever().retrieve(repo, query, intent=intent, limit=limit, filters=filters)
        merged = _merge_items(
            keyword_pack.items,
            bm25_pack.items,
            semantic_pack.items,
            keyword_weight=self.keyword_weight,
            bm25_weight=self.bm25_weight,
            semantic_weight=self.semantic_weight,
            evidence_weight=self.evidence_weight,
        )
        items = sorted(merged, key=lambda item: (-item.score, item.asset_type, item.name))[:limit]
        missing = [] if items else [f"No hybrid evidence found for query: {query}"]
        return EvidencePack(
            query=query,
            intent=intent,
            retrieval_modes=[self.name, "keyword", "bm25", "semantic"],
            items=items,
            citations=build_citations(items),
            missing_evidence=missing,
            retrieval_trace={
                "retriever": self.name,
                "candidate_count": len(merged),
                "limit": limit,
                "weights": {
                    "keyword": self.keyword_weight,
                    "bm25": self.bm25_weight,
                    "semantic": self.semantic_weight,
                    "evidence": self.evidence_weight,
                },
                "keyword_trace": keyword_pack.retrieval_trace,
                "bm25_trace": bm25_pack.retrieval_trace,
                "semantic_trace": semantic_pack.retrieval_trace,
                "semantic_enabled": True,
                "filters": filters or {},
            },
            confidence=max((item.score for item in items), default=None),
        )


def _merge_items(
    keyword_items: list[EvidenceItem],
    bm25_items: list[EvidenceItem],
    semantic_items: list[EvidenceItem],
    *,
    keyword_weight: float,
    bm25_weight: float,
    semantic_weight: float,
    evidence_weight: float,
) -> list[EvidenceItem]:
    keyword_scores = _normalized_scores(keyword_items)
    bm25_scores = _normalized_scores(bm25_items)
    semantic_scores = _normalized_scores(semantic_items)
    by_key: dict[tuple[str, str], EvidenceItem] = {}
    for item in keyword_items + bm25_items + semantic_items:
        by_key.setdefault((item.asset_type, item.asset_id), item)

    merged: list[EvidenceItem] = []
    for key, item in by_key.items():
        evidence_score = float(item.confidence or 0.0)
        score = (
            keyword_weight * keyword_scores.get(key, 0.0)
            + bm25_weight * bm25_scores.get(key, 0.0)
            + semantic_weight * semantic_scores.get(key, 0.0)
            + evidence_weight * evidence_score
        )
        merged.append(item.model_copy(update={"score": score, "retrieval_mode": "hybrid"}))
    return merged


def _normalized_scores(items: list[EvidenceItem]) -> dict[tuple[str, str], float]:
    max_score = max((item.score for item in items), default=0.0)
    if max_score <= 0:
        return {}
    return {(item.asset_type, item.asset_id): item.score / max_score for item in items}
