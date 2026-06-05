from __future__ import annotations

from collections import Counter
import math
from pathlib import Path
from typing import Any

from evolvekb.retrieval.base import EvidenceItem, EvidencePack, build_citations
from evolvekb.retrieval.keyword import build_lexical_corpus, tokenize_terms


class BM25Retriever:
    name = "bm25"

    def __init__(self, *, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b

    def retrieve(
        self,
        repo: Path,
        query: str,
        *,
        intent: str | None = None,
        limit: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> EvidencePack:
        query_terms = tokenize_terms(query)
        corpus = build_lexical_corpus(repo)
        doc_terms = [tokenize_terms(str(item.metadata.get("haystack") or item.text)) for item in corpus]
        avg_doc_length = sum(len(tokens) for tokens in doc_terms) / max(1, len(doc_terms))
        document_frequency = _document_frequency(doc_terms)
        scored_items: list[EvidenceItem] = []

        if query_terms and corpus:
            for item, terms in zip(corpus, doc_terms, strict=True):
                score = _bm25_score(
                    query_terms=query_terms,
                    document_terms=terms,
                    document_frequency=document_frequency,
                    document_count=len(corpus),
                    avg_doc_length=avg_doc_length,
                    k1=self.k1,
                    b=self.b,
                )
                if score > 0:
                    scored_items.append(item.model_copy(update={"score": score, "retrieval_mode": self.name}))

        items = sorted(scored_items, key=lambda item: (-item.score, item.asset_type, item.name))[:limit]
        missing = [] if items else [f"No BM25 evidence found for query: {query}"]
        return EvidencePack(
            query=query,
            intent=intent,
            retrieval_modes=[self.name],
            items=items,
            citations=build_citations(items),
            missing_evidence=missing,
            retrieval_trace={
                "retriever": self.name,
                "query_tokens": query_terms,
                "candidate_count": len(corpus),
                "matched_count": len(scored_items),
                "limit": limit,
                "k1": self.k1,
                "b": self.b,
                "avg_doc_length": round(avg_doc_length, 3),
                "scoring_formula": "BM25(k1=1.5, b=0.75) over local knowledge and claim corpus",
                "filters": filters or {},
            },
            confidence=max((item.score for item in items), default=None),
        )


def _document_frequency(doc_terms: list[list[str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for terms in doc_terms:
        for term in set(terms):
            counts[term] = counts.get(term, 0) + 1
    return counts


def _bm25_score(
    *,
    query_terms: list[str],
    document_terms: list[str],
    document_frequency: dict[str, int],
    document_count: int,
    avg_doc_length: float,
    k1: float,
    b: float,
) -> float:
    if not document_terms:
        return 0.0
    term_frequency = Counter(document_terms)
    score = 0.0
    doc_length = len(document_terms)
    for term in query_terms:
        tf = term_frequency.get(term, 0)
        if tf == 0:
            continue
        df = document_frequency.get(term, 0)
        idf = math.log(1 + (document_count - df + 0.5) / (df + 0.5))
        denominator = tf + k1 * (1 - b + b * doc_length / max(avg_doc_length, 1.0))
        score += idf * (tf * (k1 + 1)) / denominator
    return score
