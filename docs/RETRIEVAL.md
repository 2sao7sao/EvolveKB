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
