from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from evolvekb.evals.runner import run_evals
from evolvekb.retrieval.base import EvidencePack
from evolvekb.retrieval.bm25 import BM25Retriever
from evolvekb.retrieval.hybrid import HybridRetriever
from evolvekb.retrieval.keyword import KeywordRetriever, keyword_retrieve
from evolvekb.retrieval.semantic import SemanticRetriever


REPO = Path(__file__).resolve().parents[2]


def run_cmd(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([str(REPO), env["PYTHONPATH"]]) if env.get("PYTHONPATH") else str(REPO)
    return subprocess.run(args, cwd=REPO, env=env, text=True, capture_output=True, check=False)


def test_keyword_retriever_returns_evidence_pack() -> None:
    pack = KeywordRetriever().retrieve(REPO, "execution-first knowledge runtime", limit=5)
    assert isinstance(pack, EvidencePack)
    assert pack.retrieval_modes == ["keyword"]
    assert any(item.name == "execution-first-kb" for item in pack.items)
    assert pack.citations
    assert pack.retrieval_trace["retriever"] == "keyword"
    assert pack.retrieval_trace["candidate_count"] >= len(pack.items)
    assert EvidencePack.model_validate(pack.model_dump(mode="json"))


def test_legacy_keyword_retrieve_returns_evidence_items() -> None:
    items = keyword_retrieve(REPO, "execution-first knowledge runtime", limit=5)
    assert any(item.name == "execution-first-kb" for item in items)
    assert all(item.retrieval_mode == "keyword" for item in items)


def test_bm25_retriever_uses_same_evidence_pack_contract() -> None:
    pack = BM25Retriever().retrieve(REPO, "execution-first knowledge runtime", limit=5)
    assert pack.retrieval_modes == ["bm25"]
    assert any(item.name == "execution-first-kb" for item in pack.items)
    assert pack.retrieval_trace["retriever"] == "bm25"
    assert pack.retrieval_trace["candidate_count"] >= len(pack.items)
    assert EvidencePack.model_validate(pack.model_dump(mode="json"))


def test_hybrid_retriever_merges_local_lexical_scores() -> None:
    pack = HybridRetriever().retrieve(REPO, "execution-first knowledge runtime", limit=5)
    assert pack.retrieval_modes == ["hybrid", "keyword", "bm25"]
    assert any(item.name == "execution-first-kb" for item in pack.items)
    assert pack.retrieval_trace["semantic_enabled"] is False


def test_semantic_retriever_reports_optional_hook() -> None:
    with pytest.raises(RuntimeError, match="optional plugin hook"):
        SemanticRetriever().retrieve(REPO, "execution-first knowledge runtime")


def test_cli_query_can_select_bm25_json() -> None:
    result = run_cmd(
        sys.executable,
        "-m",
        "evolvekb.cli",
        "query",
        "execution-first knowledge runtime",
        "--retriever",
        "bm25",
        "--json",
    )
    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["retrieval_modes"] == ["bm25"]
    assert any(item["name"] == "execution-first-kb" for item in payload["items"])


def test_retrieval_eval_can_select_bm25() -> None:
    results = run_evals(REPO, ["evals/retrieval_execution_first_bm25.yaml"])
    assert results
    assert all(result.passed for result in results)
