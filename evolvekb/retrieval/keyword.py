from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from evolvekb.assets.registry import AssetRegistry
from evolvekb.retrieval.base import EvidenceItem, EvidencePack, build_citations
from evolvekb.retrieval.registry import register_retriever


TOKEN_RE = re.compile(r"[A-Za-z0-9_\-\u4e00-\u9fff]+")


def tokenize_terms(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text) if len(token) >= 2]


def tokenize(text: str) -> set[str]:
    return set(tokenize_terms(text))


@register_retriever("keyword")
class KeywordRetriever:
    name = "keyword"

    def retrieve(
        self,
        repo: Path,
        query: str,
        *,
        intent: str | None = None,
        limit: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> EvidencePack:
        query_tokens = tokenize(query)
        corpus = build_lexical_corpus(repo)
        scored_items: list[EvidenceItem] = []
        if query_tokens:
            for item in corpus:
                score = _score(query_tokens, str(item.metadata.get("haystack") or item.text))
                if score > 0:
                    scored_items.append(item.model_copy(update={"score": score, "retrieval_mode": self.name}))
        items = sorted(scored_items, key=lambda item: (-item.score, item.asset_type, item.name))[:limit]
        missing = [] if items else [f"No keyword evidence found for query: {query}"]
        return EvidencePack(
            query=query,
            intent=intent,
            retrieval_modes=[self.name],
            items=items,
            citations=build_citations(items),
            missing_evidence=missing,
            retrieval_trace={
                "retriever": self.name,
                "query_tokens": sorted(query_tokens),
                "candidate_count": len(corpus),
                "matched_count": len(scored_items),
                "limit": limit,
                "scoring_formula": "overlap(query_tokens, document_tokens) / len(query_tokens)",
                "filters": filters or {},
            },
            confidence=_pack_confidence(items),
        )


def build_lexical_corpus(repo: Path) -> list[EvidenceItem]:
    items: list[EvidenceItem] = []
    registry = AssetRegistry.load(repo)
    for block in registry.knowledge.values():
        haystack = " ".join([block.name, block.summary, " ".join(block.concepts), " ".join(block.tags)])
        items.append(
            EvidenceItem(
                asset_type="knowledge",
                asset_id=block.id,
                name=block.name,
                text=block.summary,
                score=0.0,
                retrieval_mode="corpus",
                source_ref=f"kb/knowledge/{block.name}.md",
                confidence=block.confidence,
                metadata={"haystack": haystack},
            )
        )

    for path in sorted((repo / "kb" / "claims").glob("*.jsonl")):
        for row in _read_jsonl(path):
            text = str(row.get("text") or "")
            evidence_quote = str(row.get("evidence_quote") or "")
            haystack = " ".join([text, evidence_quote])
            chunk_ids = row.get("chunk_ids") if isinstance(row.get("chunk_ids"), list) else []
            items.append(
                EvidenceItem(
                    asset_type="claim",
                    asset_id=str(row.get("id")),
                    name=str(row.get("id")),
                    text=text,
                    score=0.0,
                    retrieval_mode="corpus",
                    source_ref=str(path.relative_to(repo)),
                    source_id=str(row.get("source_id")) if row.get("source_id") else None,
                    chunk_ids=[str(chunk_id) for chunk_id in chunk_ids],
                    evidence_quote=evidence_quote or None,
                    confidence=_optional_float(row.get("confidence")),
                    metadata={"haystack": haystack},
                )
            )
    return items


def keyword_retrieve(repo: Path, query: str, limit: int = 5) -> list[EvidenceItem]:
    return KeywordRetriever().retrieve(repo, query, limit=limit).items


def evidence_pack(repo: Path, query: str, limit: int = 5) -> dict[str, Any]:
    pack = KeywordRetriever().retrieve(repo, query, limit=limit)
    data = pack.model_dump(mode="json")
    data["evidence"] = data["items"]
    return data


def _score(query_tokens: set[str], text: str) -> float:
    tokens = tokenize(text)
    if not tokens:
        return 0.0
    overlap = query_tokens & tokens
    return len(overlap) / max(1, len(query_tokens))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _pack_confidence(items: list[EvidenceItem]) -> float | None:
    if not items:
        return None
    return max(item.score for item in items)
