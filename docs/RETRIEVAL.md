# Retrieval

EvolveKB treats retrieval as evidence supply. Retrieval finds candidate evidence;
playbooks decide how that evidence becomes behavior; gates, evals, and proposals
make the behavior reviewable.

## EvidencePack Contract

All retrievers return `evolvekb.retrieval.base.EvidencePack`.

| Field | Meaning |
| --- | --- |
| `query` | User or runtime query. |
| `intent` | Optional runtime intent that requested evidence. |
| `retrieval_modes` | Ordered modes used, such as `["keyword"]` or `["hybrid", "keyword", "bm25"]`. |
| `items` | Ranked `EvidenceItem` records. |
| `citations` | Compact citation metadata for rendered output. |
| `conflicts` | Structured conflict records when retrievers disagree on the top evidence, e.g. a hybrid `keyword` + `bm25` + `semantic` merge that surfaces contradicting top items. Each entry is `{"mode": str, "items": [EvidenceItem], "note": str}`. Empty for retrievers that do not surface conflicts. |
| `missing_evidence` | Explicit reasons when no evidence is found. |
| `retrieval_trace` | Query tokens, candidate counts, limit, scoring formula, and mode-specific trace data. |
| `confidence` | Optional pack-level confidence derived from top evidence scores. |

`EvidenceItem` carries the stable fields an agent harness can depend on:

```text
asset_type, asset_id, name, text, source_ref, score, retrieval_mode,
source_id, chunk_ids, evidence_quote, confidence, freshness, metadata
```

## Built-in Modes

| Mode | Status | Dependency profile |
| --- | --- | --- |
| `keyword` | Default deterministic baseline | No external dependencies |
| `bm25` | Local lexical ranking adapter | No external dependencies |
| `semantic` | Deterministic semantic-lite ranking over token and character-ngram features | No external dependencies |
| `hybrid` | Local keyword + BM25 + semantic-lite score merge | No external dependencies |

The default quickstart remains credential-free.

## CLI

```bash
python -m evolvekb.cli query "execution-first knowledge runtime" --retriever keyword --require-evidence
python -m evolvekb.cli query "execution-first knowledge runtime" --retriever bm25 --require-evidence
python -m evolvekb.cli query "execution-first knowledge runtime" --retriever hybrid --json
```

If `--retriever` is omitted, the CLI reads `retrieval.default_mode` from the
selected settings file and falls back to `keyword`.

## Settings

```yaml
retrieval:
  default_mode: keyword
  modes:
    keyword:
      enabled: true
    bm25:
      enabled: true
    semantic:
      enabled: true
    hybrid:
      enabled: true
      weights:
        keyword: 0.35
        bm25: 0.35
        semantic: 0.2
        evidence: 0.1
```

## Eval Selection

Retrieval evals can select a mode:

```yaml
id: eval_retrieval_execution_first_bm25_001
category: retrieval_eval
input:
  query: "execution-first knowledge runtime"
  retriever: bm25
expected:
  must_retrieve:
    - execution-first-kb
  limit: 5
```

## Boundaries

- Keyword and BM25 are lexical baselines, not semantic-search superiority claims.
- The built-in semantic mode is deterministic semantic-lite ranking, not an
  embedding model or vector database.
- Hybrid merges local keyword, BM25, semantic-lite, and evidence-confidence scores.
- Retrieval scores are used for evidence ranking. They do not replace gates,
  evals, proposal review, or playbook-specific safety rules.

## Pluggable Adapters

Retrieval modes are resolved through a runtime registry so downstream projects
can ship additional modes without forking the core.

### Register A Mode

Use the `register_retriever` decorator on a class that follows the
`Retriever` protocol (an instance attribute `name` plus a `retrieve(...)`
method returning an `EvidencePack`):

```python
from evolvekb.retrieval.registry import register_retriever


@register_retriever("my-mode")
class MyRetriever:
    name = "my-mode"

    def retrieve(self, repo, query, *, intent=None, limit=5, filters=None):
        ...
```

Or call `register_retriever_class("my-mode", MyRetriever)` at runtime
(e.g. from a `pyproject.toml` entry point).

### Built-in Modes

These are registered automatically when `evolvekb.retrieval` is imported:

| Mode | Source | Notes |
| --- | --- | --- |
| `keyword` | `evolvekb.retrieval.keyword.KeywordRetriever` | Deterministic token overlap. |
| `bm25` | `evolvekb.retrieval.bm25.BM25Retriever` | Local BM25 with `k1` / `b` constructor kwargs. |
| `semantic` | `evolvekb.retrieval.semantic.SemanticRetriever` | Deterministic semantic-lite over token + char-ngram features. |
| `hybrid` | `evolvekb.retrieval.hybrid.HybridRetriever` | Weighted merge of keyword / bm25 / semantic / evidence. |

### Contrib Modes

Optional adapters live under `evolvekb.retrieval.contrib`. They are
registered by importing the sub-package (already done in
`evolvekb.retrieval.__init__`):

| Mode | Source | Notes |
| --- | --- | --- |
| `tfidf` | `evolvekb.retrieval.contrib.tfidf.TFIDFRetriever` | Zero-dependency TF-IDF. `sublinear_tf` and `min_token_length` are forwarded as constructor kwargs from `get_retriever(..., config=...)`. |

### Settings

Settings files can declare an extra mode. The `class` field is advisory
documentation for now; resolution still goes through the registry by `name`:

```yaml
retrieval:
  default_mode: keyword
  modes:
    tfidf:
      enabled: true
      class: evolvekb.retrieval.contrib.tfidf:TFIDFRetriever
      config:
        sublinear_tf: true
        min_token_length: 2
```

### CLI

Once a mode is registered, it is usable everywhere a retriever name is
expected:

```bash
python -m evolvekb.cli query "execution-first knowledge" --retriever tfidf
python -m evolvekb.cli query "execution-first knowledge" --retriever my-mode
```

`get_retriever("bm25", config={"k1": 2.0})` forwards `config` to the
retriever constructor, so a mode can read its own settings without the
runtime hard-coding keys.
