from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    asset_type: Literal["knowledge", "claim", "usage", "skill", "source_chunk"]
    asset_id: str
    name: str
    text: str
    source_ref: str
    score: float = Field(ge=0.0)
    retrieval_mode: str
    source_id: str | None = None
    chunk_ids: list[str] = Field(default_factory=list)
    evidence_quote: str | None = None
    confidence: float | None = None
    freshness: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidencePack(BaseModel):
    query: str
    intent: str | None = None
    retrieval_modes: list[str]
    items: list[EvidenceItem]
    citations: list[dict[str, Any]] = Field(default_factory=list)
    conflicts: list[dict[str, Any]] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    retrieval_trace: dict[str, Any] = Field(default_factory=dict)
    confidence: float | None = None


class Retriever(Protocol):
    name: str

    def retrieve(
        self,
        repo: Path,
        query: str,
        *,
        intent: str | None = None,
        limit: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> EvidencePack:
        ...


def build_citations(items: list[EvidenceItem]) -> list[dict[str, Any]]:
    return [
        {
            "asset_type": item.asset_type,
            "asset_id": item.asset_id,
            "name": item.name,
            "source_ref": item.source_ref,
            "score": round(item.score, 3),
            "retrieval_mode": item.retrieval_mode,
            "source_id": item.source_id,
            "chunk_ids": item.chunk_ids,
        }
        for item in items
    ]
