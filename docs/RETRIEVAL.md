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
| `hybrid` | Local keyword + BM25 score merge | No external dependencies |
| `semantic` | Optional plugin hook | Disabled until an embedding implementation is configured |

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
      enabled: false
    hybrid:
      enabled: true
      weights:
        keyword: 0.5
        bm25: 0.4
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
- Hybrid currently merges local lexical scores and evidence confidence; semantic
  score merging is a future optional extension.
- Retrieval scores are used for evidence ranking. They do not replace gates,
  evals, proposal review, or playbook-specific safety rules.
