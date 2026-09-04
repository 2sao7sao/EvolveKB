"""Deterministic TF-IDF retriever.

Uses the same lexical corpus as :mod:`evolvekb.retrieval.keyword` and scores
each document by summed term-frequency-inverse-document-frequency. The
``sublinear_tf`` and ``min_token_length`` parameters can be tuned at
construction time and are forwarded from ``get_retriever(..., config=...)``
so settings can override the defaults without code changes.

This retriever is intentionally zero-dependency. It exists to prove the
pluggable registry contract: a downstream project can ship its own
``@register_retriever("...")`` class and use it through the same
``evolvekb.cli query --retriever ...`` path.
"""
from __future__ import annotations

import math
from collections import Counter
from pathlib import Path
from typing import Any

from evolvekb.retrieval.base import EvidenceItem, EvidencePack, build_citations
from evolvekb.retrieval.keyword import build_lexical_corpus, tokenize_terms
from evolvekb.retrieval.registry import register_retriever


@register_retriever("tfidf")
class TFIDFRetriever:
    name = "tfidf"

    def __init__(
        self,
        *,
        sublinear_tf: bool = True,
        min_token_length: int = 2,
    ):
        self.sublinear_tf = sublinear_tf
        self.min_token_length = min_token_length

    def retrieve(
        self,
        repo: Path,
        query: str,
        *,
        intent: str | None = None,
        limit: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> EvidencePack:
        query_terms = [
            term
            for term in tokenize_terms(query)
            if len(term) >= self.min_token_length
        ]
        corpus = build_lexical_corpus(repo)
        doc_terms = [
            [
                term
                for term in tokenize_terms(str(item.metadata.get("haystack") or item.text))
                if len(term) >= self.min_token_length
            ]
            for item in corpus
        ]
        document_frequency = _document_frequency(doc_terms)
        scored_items: list[EvidenceItem] = []
        if query_terms and corpus:
            for item, terms in zip(corpus, doc_terms, strict=True):
                score = _tfidf_score(
                    query_terms=query_terms,
                    document_terms=terms,
                    document_frequency=document_frequency,
                    document_count=len(corpus),
                    sublinear_tf=self.sublinear_tf,
                )
                if score > 0:
                    scored_items.append(
                        item.model_copy(
                            update={"score": score, "retrieval_mode": self.name}
                        )
                    )
        items = sorted(scored_items, key=lambda item: (-item.score, item.asset_type, item.name))[:limit]
        missing = [] if items else [f"No TF-IDF evidence found for query: {query}"]
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
                "sublinear_tf": self.sublinear_tf,
                "min_token_length": self.min_token_length,
                "scoring_formula": "sum(tfidf(term, doc) for term in query_terms)",
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


def _tfidf_score(
    *,
    query_terms: list[str],
    document_terms: list[str],
    document_frequency: dict[str, int],
    document_count: int,
    sublinear_tf: bool,
) -> float:
    if not document_terms:
        return 0.0
    term_frequency = Counter(document_terms)
    score = 0.0
    for term in query_terms:
        tf = term_frequency.get(term, 0)
        if tf == 0:
            continue
        df = document_frequency.get(term, 0)
        # Smoothed IDF so unseen terms do not produce -inf in tiny corpora.
        idf = math.log((1 + document_count) / (1 + df)) + 1.0
        tf_value = 1.0 + math.log(tf) if sublinear_tf else float(tf)
        score += idf * tf_value
    return score
