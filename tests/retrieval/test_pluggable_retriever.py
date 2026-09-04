"""Tests for the pluggable retriever registry (v0.4 track)."""
from __future__ import annotations

from pathlib import Path

import pytest

from evolvekb.retrieval import available_retrievers, get_retriever
from evolvekb.retrieval.contrib import TFIDFRetriever
from evolvekb.retrieval.registry import (
    _REGISTRY,
    register_retriever,
    register_retriever_class,
    unregister_retriever,
)


@pytest.fixture(autouse=True)
def _isolate_registry():
    """Snapshot/restore the registry around each test so decorators in other
    test modules cannot leak into these assertions."""

    snapshot = dict(_REGISTRY)
    try:
        yield
    finally:
        _REGISTRY.clear()
        _REGISTRY.update(snapshot)


def test_builtin_retrievers_registered_at_import():
    names = set(available_retrievers())
    assert {"keyword", "bm25", "semantic", "hybrid"}.issubset(names)


def test_get_retriever_returns_instance_with_default_constructor():
    retriever = get_retriever("bm25")
    assert retriever.name == "bm25"


def test_get_retriever_forwards_config_as_kwargs():
    retriever = get_retriever("bm25", config={"k1": 2.0, "b": 0.5})
    assert retriever.k1 == 2.0
    assert retriever.b == 0.5


def test_unknown_retriever_raises_with_helpful_message():
    with pytest.raises(ValueError) as excinfo:
        get_retriever("nope-mode")
    message = str(excinfo.value)
    assert "Unknown retriever" in message
    assert "nope-mode" in message
    # Available retrievers should be listed for actionable diagnostics.
    assert "keyword" in message
    assert "tfidf" in message


def test_decorator_registers_custom_retriever():
    @register_retriever("probe-mode")
    class ProbeRetriever:
        name = "probe-mode"

        def retrieve(self, repo, query, *, intent=None, limit=5, filters=None):
            raise NotImplementedError

    assert "probe-mode" in available_retrievers()
    assert isinstance(get_retriever("probe-mode"), ProbeRetriever)


def test_runtime_registration_works():
    class LateRetriever:
        name = "late-mode"

        def retrieve(self, repo, query, *, intent=None, limit=5, filters=None):
            raise NotImplementedError

    register_retriever_class("late-mode", LateRetriever)
    assert isinstance(get_retriever("late-mode"), LateRetriever)


def test_double_registration_same_class_is_idempotent():
    @register_retriever("idempotent-mode")
    class IdempotentRetriever:
        name = "idempotent-mode"

        def retrieve(self, repo, query, *, intent=None, limit=5, filters=None):
            raise NotImplementedError

    # Re-applying the decorator to the same class should not raise.
    decorated_again = register_retriever("idempotent-mode")(IdempotentRetriever)
    assert decorated_again is IdempotentRetriever


def test_collision_with_different_class_raises():
    @register_retriever("collision-mode")
    class FirstRetriever:
        name = "collision-mode"

        def retrieve(self, repo, query, *, intent=None, limit=5, filters=None):
            raise NotImplementedError

    class SecondRetriever:
        name = "collision-mode"

        def retrieve(self, repo, query, *, intent=None, limit=5, filters=None):
            raise NotImplementedError

    with pytest.raises(ValueError, match="already registered"):
        register_retriever_class("collision-mode", SecondRetriever)


def test_unregister_removes_retriever():
    register_retriever_class("transient-mode", type("T", (), {"name": "transient-mode", "retrieve": lambda self, *a, **kw: None})())
    assert "transient-mode" in available_retrievers()
    unregister_retriever("transient-mode")
    assert "transient-mode" not in available_retrievers()


def test_contrib_tfidf_retriever_works_on_repo(repo_cwd: Path):
    """End-to-end probe: the contrib TF-IDF adapter returns an EvidencePack."""

    pack = get_retriever("tfidf").retrieve(repo_cwd, "execution-first knowledge", limit=3)
    assert pack.retrieval_modes == ["tfidf"]
    assert pack.items, "tfidf should return at least one item for the seed query"
    assert all(item.retrieval_mode == "tfidf" for item in pack.items)
    assert pack.retrieval_trace["scoring_formula"].startswith("sum(tfidf")


def test_contrib_tfidf_accepts_config_kwargs():
    retriever = get_retriever(
        "tfidf",
        config={"sublinear_tf": False, "min_token_length": 3},
    )
    assert isinstance(retriever, TFIDFRetriever)
    assert retriever.sublinear_tf is False
    assert retriever.min_token_length == 3


def test_contrib_regex_retriever_works_on_repo(repo_cwd: Path):
    """Regex retriever matches corpus text against the query as a regex pattern."""

    pack = get_retriever("regex").retrieve(repo_cwd, r"execution.first|knowledge", limit=5)
    assert pack.retrieval_modes == ["regex"]
    assert pack.items, "regex should match seed corpus"
    assert all(item.retrieval_mode == "regex" for item in pack.items)
    # The pattern stored in the trace is the same regex string the caller passed in.
    assert pack.retrieval_trace["pattern"] == r"execution.first|knowledge"


def test_contrib_regex_respects_case_sensitivity():
    from evolvekb.retrieval.contrib.regex import RegexRetriever

    case_sensitive = RegexRetriever(case_sensitive=True).retrieve(
        Path("."), "Execution", limit=5
    )
    case_insensitive = RegexRetriever(case_sensitive=False).retrieve(
        Path("."), "Execution", limit=5
    )
    assert len(case_insensitive.items) >= len(case_sensitive.items)


def test_contrib_regex_rejects_invalid_pattern():
    from evolvekb.retrieval.contrib.regex import RegexRetriever

    retriever = RegexRetriever()
    with pytest.raises(ValueError, match="Invalid regex"):
        retriever.retrieve(Path("."), "(unclosed", limit=5)


def test_contrib_regex_rejects_bad_score_normalize():
    from evolvekb.retrieval.contrib.regex import RegexRetriever

    with pytest.raises(ValueError, match="score_normalize"):
        RegexRetriever(score_normalize="bogus")


def test_contrib_regex_binary_score_normalize():
    from evolvekb.retrieval.contrib.regex import RegexRetriever

    pack = RegexRetriever(score_normalize="binary").retrieve(
        Path("."), "knowledge", limit=5
    )
    assert all(item.score == 1.0 for item in pack.items)


def test_contrib_tfidf_cli_query_path(monkeypatch: pytest.MonkeyPatch):
    """The CLI ``--retriever tfidf`` path must work the same as a built-in mode."""

    from evolvekb.cli import main

    captured: dict[str, str] = {}

    def fake_query(args):
        captured["retriever"] = args.retriever or "keyword"
        return 0

    monkeypatch.setattr("evolvekb.cli.cmd_query", fake_query)
    rc = main(["query", "anything", "--retriever", "tfidf", "--limit", "1"])
    assert rc == 0
    assert captured["retriever"] == "tfidf"


@pytest.fixture
def repo_cwd() -> Path:
    """Return the EvolveKB repo root (cwd of the test invocation)."""

    return Path(__file__).resolve().parents[2]
