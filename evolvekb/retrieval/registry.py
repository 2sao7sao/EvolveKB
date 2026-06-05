from __future__ import annotations

from evolvekb.retrieval.base import Retriever
from evolvekb.retrieval.bm25 import BM25Retriever
from evolvekb.retrieval.hybrid import HybridRetriever
from evolvekb.retrieval.keyword import KeywordRetriever
from evolvekb.retrieval.semantic import SemanticRetriever


def get_retriever(name: str | None = None) -> Retriever:
    mode = (name or "keyword").strip().lower()
    if mode == "keyword":
        return KeywordRetriever()
    if mode == "bm25":
        return BM25Retriever()
    if mode == "hybrid":
        return HybridRetriever()
    if mode == "semantic":
        return SemanticRetriever()
    raise ValueError(f"Unknown retriever '{name}'. Expected one of: keyword, bm25, hybrid, semantic")


def available_retrievers() -> list[str]:
    return ["keyword", "bm25", "hybrid", "semantic"]
