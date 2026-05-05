from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from evolvekb.assets.registry import AssetRegistry


TOKEN_RE = re.compile(r"[A-Za-z0-9_\-\u4e00-\u9fff]+")


@dataclass
class EvidenceItem:
    asset_type: str
    asset_id: str
    name: str
    text: str
    score: float
    source_ref: str


def tokenize(text: str) -> set[str]:
    return {token.lower() for token in TOKEN_RE.findall(text) if len(token) >= 2}


def keyword_retrieve(repo: Path, query: str, limit: int = 5) -> list[EvidenceItem]:
    query_tokens = tokenize(query)
    if not query_tokens:
        return []
    items: list[EvidenceItem] = []
    registry = AssetRegistry.load(repo)
    for block in registry.knowledge.values():
        haystack = " ".join([block.name, block.summary, " ".join(block.concepts), " ".join(block.tags)])
        score = _score(query_tokens, haystack)
        if score > 0:
            items.append(
                EvidenceItem(
                    asset_type="knowledge",
                    asset_id=block.id,
                    name=block.name,
                    text=block.summary,
                    score=score,
                    source_ref=f"kb/knowledge/{block.name}.md",
                )
            )

    for path in sorted((repo / "kb" / "claims").glob("*.jsonl")):
        for row in _read_jsonl(path):
            text = str(row.get("text") or "")
            score = _score(query_tokens, text)
            if score > 0:
                items.append(
                    EvidenceItem(
                        asset_type="claim",
                        asset_id=str(row.get("id")),
                        name=str(row.get("id")),
                        text=text,
                        score=score,
                        source_ref=str(path.relative_to(repo)),
                    )
                )
    return sorted(items, key=lambda item: (-item.score, item.asset_type, item.name))[:limit]


def evidence_pack(repo: Path, query: str, limit: int = 5) -> dict[str, Any]:
    items = keyword_retrieve(repo, query, limit=limit)
    return {
        "query": query,
        "retrieval_modes": ["keyword"],
        "citations": [
            {
                "asset_type": item.asset_type,
                "asset_id": item.asset_id,
                "name": item.name,
                "source_ref": item.source_ref,
                "score": round(item.score, 3),
            }
            for item in items
        ],
        "evidence": [item.__dict__ for item in items],
    }


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
