# Real-corpus validation (pilot)

This directory holds the first evaluation that uses a real corpus instead of the
synthetic refund-policy seeds.

## What is measured

Three systems answer the same 10 questions over the repository's own documentation
(10 markdown files, about 28 KB). The corpus is real, versioned, and not part of a
public benchmark, which limits memorisation from the model's pretraining.

| System | Context given to the answerer |
| --- | --- |
| `long_context` | every document concatenated |
| `bm25_rag` | top 4 chunks from an independent BM25 implementation |
| `kb_evidence` | top 4 evidence items returned by `evolvekb query --retriever bm25` |

Each answer is scored 0/1/2 by a second model call against a written reference
answer, and the runner also records whether the answer cites the gold document.

## Limits

- One corpus, 10 questions, one model, one run. This is a pilot, not a benchmark.
- The corpus is the project's own documentation, so questions are about EvolveKB
  rather than about an external domain.
- Scores come from an LLM judge; a human should spot-check any claim that matters.
