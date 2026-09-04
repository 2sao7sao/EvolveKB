"""Regex-based retriever.

The query is treated as a regular expression (not a natural-language query)
and each candidate text is matched against it. The score is the number of
matches normalized by the haystack length so longer documents do not get an
unfairly high raw score.

This is useful for narrowly scoped agents that need to surface knowledge
assets matching a structural pattern (e.g. all policies mentioning a specific
SKU, all claims containing a particular regex token). It is **not** a general
replacement for lexical or semantic retrieval.

The retriever validates ``re.compile`` at construction time so configuration
errors surface immediately rather than at query time.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from evolvekb.retrieval.base import EvidenceItem, EvidencePack, build_citations
from evolvekb.retrieval.keyword import build_lexical_corpus
from evolvekb.retrieval.registry import register_retriever


@register_retriever("regex")
class RegexRetriever:
    name = "regex"

    def __init__(
        self,
        *,
        case_sensitive: bool = False,
        min_matches: int = 1,
        score_normalize: str = "per_1k_chars",
    ):
        if score_normalize not in {"raw", "per_1k_chars", "binary"}:
            raise ValueError(
                f"score_normalize must be one of raw / per_1k_chars / binary, got {score_normalize!r}"
            )
        self.case_sensitive = case_sensitive
        self.min_matches = min_matches
        self.score_normalize = score_normalize

    def retrieve(
        self,
        repo: Path,
        query: str,
        *,
        intent: str | None = None,
        limit: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> EvidencePack:
        flags = 0 if self.case_sensitive else re.IGNORECASE
        try:
            pattern = re.compile(query, flags)
        except re.error as exc:
            raise ValueError(f"Invalid regex for retriever 'regex': {exc}") from exc

        corpus = build_lexical_corpus(repo)
        scored_items: list[EvidenceItem] = []
        for item in corpus:
            text = str(item.metadata.get("haystack") or item.text)
            matches = pattern.findall(text)
            if len(matches) < self.min_matches:
                continue
            score = _score(matches, len(text), self.score_normalize)
            scored_items.append(
                item.model_copy(update={"score": score, "retrieval_mode": self.name})
            )

        items = sorted(scored_items, key=lambda item: (-item.score, item.asset_type, item.name))[:limit]
        missing = [] if items else [f"No regex match for pattern: {query!r}"]
        return EvidencePack(
            query=query,
            intent=intent,
            retrieval_modes=[self.name],
            items=items,
            citations=build_citations(items),
            missing_evidence=missing,
            retrieval_trace={
                "retriever": self.name,
                "pattern": pattern.pattern,
                "case_sensitive": self.case_sensitive,
                "min_matches": self.min_matches,
                "score_normalize": self.score_normalize,
                "candidate_count": len(corpus),
                "matched_count": len(scored_items),
                "limit": limit,
                "filters": filters or {},
            },
            confidence=max((item.score for item in items), default=None),
        )


def _score(matches: list[str], text_length: int, mode: str) -> float:
    if mode == "binary":
        return 1.0
    if mode == "raw":
        return float(len(matches))
    # per_1k_chars: matches per 1000 chars, so a doc with 1 match in 200 chars
    # scores 5.0 while a doc with 1 match in 5000 chars scores 0.2.
    return len(matches) * 1000.0 / max(text_length, 1)
