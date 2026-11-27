from __future__ import annotations

import json
from pathlib import Path

from evolvekb.gates.engine import validate_claim_evidence


def _write_chunk(repo: Path, chunk_id: str, text: str) -> None:
    directory = repo / "kb" / "chunks"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "src.jsonl").write_text(
        json.dumps({"id": chunk_id, "text": text}) + "\n", encoding="utf-8")


def _write_claim(repo: Path, *, quote: str, chunk_ids: list[str]) -> None:
    directory = repo / "kb" / "claims"
    directory.mkdir(parents=True, exist_ok=True)
    row = {"id": "claim_1", "status": "active", "source_id": "src",
           "chunk_ids": chunk_ids, "text": "claim text", "evidence_quote": quote}
    (directory / "src.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")


def _failures(repo: Path):
    return [result for result in validate_claim_evidence(repo) if not result.passed]


def test_fabricated_quote_is_blocked(tmp_path: Path) -> None:
    _write_chunk(tmp_path, "chunk_1", "Refunds are allowed within 30 days of purchase.")
    _write_claim(tmp_path, quote="Refunds are allowed within 60 days of purchase.",
                 chunk_ids=["chunk_1"])

    failures = _failures(tmp_path)

    assert len(failures) == 1
    assert failures[0].gate_id == "claim_evidence_quote_matches_chunk"
    assert failures[0].severity == "blocker"


def test_quote_present_in_chunk_passes(tmp_path: Path) -> None:
    _write_chunk(tmp_path, "chunk_1", "Refunds are allowed within 30 days of purchase.")
    _write_claim(tmp_path, quote="Refunds are allowed within 30 days of purchase.",
                 chunk_ids=["chunk_1"])

    assert _failures(tmp_path) == []


def test_markdown_noise_does_not_break_matching(tmp_path: Path) -> None:
    _write_chunk(tmp_path, "chunk_1", "Use **BM25** for lexical ranking; hybrid for merges.")
    _write_claim(tmp_path, quote="Use BM25 for lexical ranking; hybrid for merges.",
                 chunk_ids=["chunk_1"])

    assert _failures(tmp_path) == []


def test_claim_pointing_at_unknown_chunk_is_blocked(tmp_path: Path) -> None:
    _write_chunk(tmp_path, "chunk_1", "Refunds are allowed within 30 days of purchase.")
    _write_claim(tmp_path, quote="Refunds are allowed within 30 days of purchase.",
                 chunk_ids=["chunk_missing"])

    failures = _failures(tmp_path)

    assert len(failures) == 1
    assert failures[0].gate_id == "claim_evidence_quote_matches_chunk"


def test_repo_without_chunk_store_keeps_legacy_behaviour(tmp_path: Path) -> None:
    _write_claim(tmp_path, quote="Anything, because there is no chunk store.",
                 chunk_ids=["chunk_1"])

    assert _failures(tmp_path) == []
