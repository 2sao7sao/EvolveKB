from __future__ import annotations

from pathlib import Path
from typing import Any

from evolvekb.retrieval.base import EvidencePack


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
        raise RuntimeError(
            "semantic retriever is an optional plugin hook and is not enabled in the "
            "default install. Use --retriever keyword or --retriever bm25, or configure "
            "a semantic retriever implementation."
        )
