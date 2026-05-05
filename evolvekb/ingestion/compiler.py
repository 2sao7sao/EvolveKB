from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from evolvekb.assets.hashing import stable_hash
from evolvekb.core.models import Claim, Concept, KnowledgeBlock, SourceChunk, SourceDocument
from evolvekb.wiki import append_kb_log, rebuild_kb_index


WORD_RE = re.compile(r"[A-Za-z0-9_\-\u4e00-\u9fff]+")
SENTENCE_RE = re.compile(r"(?<=[.!?。！？])\s+")


@dataclass
class IngestResult:
    source: SourceDocument
    chunks: list[SourceChunk]
    claims: list[Claim]
    concepts: list[Concept]
    knowledge: KnowledgeBlock
    knowledge_path: Path | None
    proposal_path: Path | None


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", value.lower()).strip("-")
    return slug or "document"


def parse_markdown_sections(text: str) -> list[tuple[list[str], str]]:
    sections: list[tuple[list[str], list[str]]] = [([], [])]
    heading_path: list[str] = []
    for line in text.splitlines():
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            title = line.lstrip("#").strip()
            if title:
                heading_path = heading_path[: max(0, level - 1)] + [title]
                sections.append((heading_path.copy(), []))
            continue
        sections[-1][1].append(line)
    out: list[tuple[list[str], str]] = []
    for path, lines in sections:
        body = "\n".join(lines).strip()
        if body:
            out.append((path, body))
    return out


def chunk_markdown(source_id: str, text: str, max_chars: int = 1200) -> list[SourceChunk]:
    chunks: list[SourceChunk] = []
    for heading_path, body in parse_markdown_sections(text):
        start = 0
        while start < len(body):
            piece = body[start : start + max_chars].strip()
            if piece:
                chunk_id = f"chunk_{source_id}_{len(chunks) + 1:04d}"
                chunks.append(
                    SourceChunk(
                        id=chunk_id,
                        source_id=source_id,
                        chunk_index=len(chunks),
                        heading_path=heading_path,
                        text=piece,
                        token_count=len(WORD_RE.findall(piece)),
                        char_start=start,
                        char_end=start + len(piece),
                        embedding_text=" ".join(heading_path + [piece]),
                    )
                )
            start += max_chars
    if not chunks and text.strip():
        chunks.append(
            SourceChunk(
                id=f"chunk_{source_id}_0001",
                source_id=source_id,
                chunk_index=0,
                heading_path=[],
                text=text.strip(),
                token_count=len(WORD_RE.findall(text)),
                embedding_text=text.strip(),
            )
        )
    return chunks


def extract_claims(source_id: str, chunks: list[SourceChunk], limit: int = 24) -> list[Claim]:
    claims: list[Claim] = []
    for chunk in chunks:
        sentences = [part.strip() for part in SENTENCE_RE.split(chunk.text) if part.strip()]
        if not sentences:
            sentences = [line.strip() for line in chunk.text.splitlines() if line.strip()]
        for sentence in sentences:
            if len(sentence) < 24:
                continue
            claim_id = f"claim_{source_id}_{len(claims) + 1:04d}"
            claims.append(
                Claim(
                    id=claim_id,
                    source_id=source_id,
                    chunk_ids=[chunk.id],
                    text=sentence[:500],
                    claim_type=_guess_claim_type(sentence),
                    confidence=0.55,
                    evidence_quote=sentence[:240],
                    status="active",
                    metadata={"extractor": "deterministic_sentence_v1"},
                )
            )
            if len(claims) >= limit:
                return claims
    return claims


def _guess_claim_type(sentence: str) -> str:
    lower = sentence.lower()
    if "must" in lower or "should" in lower or "必须" in sentence or "应该" in sentence:
        return "principle"
    if "how to" in lower or "步骤" in sentence or "流程" in sentence:
        return "procedure"
    if "tradeoff" in lower or "权衡" in sentence:
        return "tradeoff"
    if "example" in lower or "例如" in sentence:
        return "example"
    if " is " in lower or "是" in sentence:
        return "definition"
    return "fact"


def extract_concepts(source_id: str, title: str, chunks: list[SourceChunk], claims: list[Claim]) -> list[Concept]:
    counts: dict[str, int] = {}
    for token in WORD_RE.findall(" ".join([title] + [c.text for c in chunks] + [c.text for c in claims])):
        if len(token) < 3:
            continue
        key = token.strip("-_").lower()
        if not key or key.isdigit():
            continue
        counts[key] = counts.get(key, 0) + 1
    names = [name for name, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:12]]
    concepts: list[Concept] = []
    for name in names:
        concepts.append(
            Concept(
                id=f"concept_{source_id}_{slugify(name).replace('-', '_')}",
                name=name,
                aliases=[],
                description=f"Extracted concept from {title}.",
                related_claim_ids=[claim.id for claim in claims if name in claim.text.lower()][:8],
                related_knowledge_ids=[f"kb_{source_id}"],
            )
        )
    return concepts


def compile_markdown(
    repo: Path,
    doc_path: str | Path,
    write: bool = True,
    proposal: bool = False,
) -> IngestResult:
    path = Path(doc_path)
    if not path.is_absolute():
        path = repo / path
    if not path.exists():
        raise FileNotFoundError(f"Document not found: {path}")

    text = path.read_text(encoding="utf-8", errors="ignore")
    title = _extract_title(text) or path.stem
    name = slugify(path.stem)
    source_id = f"src_{stable_hash({'path': str(path), 'text': text})[:12]}"
    now = datetime.now(timezone.utc)
    source = SourceDocument(
        id=source_id,
        uri=str(path),
        source_type="markdown" if path.suffix.lower() in {".md", ".markdown"} else "txt",
        title=title,
        ingested_at=now,
        content_hash=stable_hash(text),
        metadata={"compiler": "deterministic_markdown_v1"},
    )
    chunks = chunk_markdown(source_id, text)
    claims = extract_claims(source_id, chunks)
    concepts = extract_concepts(source_id, title, chunks, claims)
    knowledge = KnowledgeBlock(
        id=f"kb_{name.replace('-', '_')}",
        name=name,
        block_type="reference",
        source_refs=[{"source_id": source.id, "chunk_ids": [chunk.id for chunk in chunks]}],
        summary=_summary_from_chunks(chunks),
        claims=[claim.id for claim in claims],
        concepts=[concept.name for concept in concepts],
        source_ids=[source.id],
        chunk_ids=[chunk.id for chunk in chunks],
        confidence=0.6 if claims else 0.4,
        updated_at=now.date(),
        version=1,
        tags=[],
        recommended_usage=[],
        status="active",
        metadata={"compiler": "deterministic_markdown_v1"},
    )

    knowledge_path = None
    proposal_path = None
    if write:
        _write_json(repo / "kb" / "sources" / f"{source.id}.json", source.model_dump(mode="json"))
        _write_jsonl(repo / "kb" / "chunks" / f"{source.id}.jsonl", [c.model_dump(mode="json") for c in chunks])
        _write_jsonl(repo / "kb" / "claims" / f"{source.id}.jsonl", [c.model_dump(mode="json") for c in claims])
        _write_jsonl(
            repo / "kb" / "concepts" / f"{source.id}.jsonl",
            [c.model_dump(mode="json") for c in concepts],
        )
        if proposal:
            proposal_path = _write_ingest_proposal(repo, knowledge, claims)
        else:
            knowledge_path = _write_knowledge(repo / "kb" / "knowledge" / f"{knowledge.name}.md", knowledge)
            rebuild_kb_index(repo)
        append_kb_log(repo, "ingest", f"Compiled {path.name} into {knowledge.name}")

    return IngestResult(source, chunks, claims, concepts, knowledge, knowledge_path, proposal_path)


def _extract_title(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("#"):
            title = line.lstrip("#").strip()
            if title:
                return title
    return None


def _summary_from_chunks(chunks: list[SourceChunk]) -> str:
    if not chunks:
        return "N/A"
    text = re.sub(r"\s+", " ", chunks[0].text).strip()
    return text[:280] or "N/A"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _write_knowledge(path: Path, knowledge: KnowledgeBlock) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fm = knowledge.model_dump(mode="json", exclude_none=True)
    body = [
        f"# {knowledge.name}",
        "",
        "## Summary",
        knowledge.summary,
        "",
        "## Claims",
    ]
    body.extend([f"- `{claim_id}`" for claim_id in knowledge.claims] or ["- none"])
    path.write_text(
        "---\n"
        + yaml.safe_dump(fm, sort_keys=False, allow_unicode=True).strip()
        + "\n---\n\n"
        + "\n".join(body)
        + "\n",
        encoding="utf-8",
    )
    return path


def _write_ingest_proposal(repo: Path, knowledge: KnowledgeBlock, claims: list[Claim]) -> Path:
    from evolvekb.evolution.proposal import create_write_file_proposal

    knowledge_payload = yaml.safe_dump(
        knowledge.model_dump(mode="json", exclude_none=True),
        sort_keys=False,
        allow_unicode=True,
    ).strip()
    body = f"---\n{knowledge_payload}\n---\n\n# {knowledge.name}\n\n## Summary\n{knowledge.summary}\n"
    return create_write_file_proposal(
        repo=repo,
        title=f"Ingest {knowledge.name}",
        proposal_type="knowledge_update",
        path=f"kb/knowledge/{knowledge.name}.md",
        content=body,
        rationale="Compiled source document into evidence-backed knowledge asset.",
        evidence_ids=[claim.id for claim in claims],
    )
