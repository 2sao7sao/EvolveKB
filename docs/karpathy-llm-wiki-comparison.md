# Karpathy LLM Wiki Reference Notes

Source: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

## Summary

Karpathy's LLM Wiki pattern proposes a personal knowledge base where raw sources stay immutable, an LLM-maintained markdown wiki accumulates synthesis, and a schema file teaches the agent how to ingest, query, lint, index, and log updates.

EvolveKB shares the same rejection of query-time-only RAG: knowledge should be compiled and maintained once, then reused. The main difference is that EvolveKB separates the compiled artifact into `knowledge`, `usage`, and `skills`, and treats evolution as a gated runtime concern instead of a free-form wiki editing loop.

## Key Differences

- Karpathy's pattern is wiki-first: pages, wikilinks, index, log, and human browsing are the central interface.
- EvolveKB is runtime-first: knowledge blocks, usage assets, skills, settings, gates, and proposals are the central interface.
- Karpathy's pattern lets the LLM own the wiki layer directly; EvolveKB should let the model propose updates, while gates and review control canonical mutation.
- Karpathy's pattern uses `index.md` and `log.md` as lightweight navigation and memory; EvolveKB previously had usage index/events but lacked a repo-wide KB index and chronological KB log.
- Karpathy's pattern can stay useful without embeddings at moderate scale; EvolveKB should preserve that advantage by making file/index/graph traversal first-class before adding vector retrieval.

## Borrowed Optimizations

- Add a repo-wide `kb/index.md` generated from knowledge, usage, and skill assets.
- Add append-only `kb/log.md` entries for index rebuilds, runs, ingests, reviews, and future proposals.
- Add a lint command that checks broken references, missing playbooks, and orphan knowledge blocks.
- Keep raw source documents immutable when ingestion compiler work begins.
- Treat good query outputs as candidate knowledge or usage updates, but route them through proposals and gates.

## Product Direction

EvolveKB should not become a normal RAG wrapper. Its sharper position is:

> A self-iterating knowledge-to-skill runtime where the model understands, records, validates, and evolves both knowledge and usage.

The next implementation step after Milestone 1+2 is to make self-iteration explicit:

- `ingest` compiles source material into knowledge candidates.
- `query/run` produces traceable outputs.
- `lint` finds gaps, stale references, or orphan assets.
- `proposal` converts useful discoveries into reviewable patches.
- `index` and `log` preserve navigability and evolution history without requiring vector infrastructure.
