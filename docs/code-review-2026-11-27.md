# Code review, external comparison, and the first real-corpus evaluation

Date: 2026-11-27. Scope: `evolvekb/` runtime, asset model, gates, evals, and the
knowledge assets under `kb/`. External comparison: RAG, agentic RAG, LLM-wiki,
agent-memory, and self-improving-agent literature up to late 2026.

Method: read the runtime and gates, run the seed suites, then run a new evaluation
over a real corpus with two independent baselines and a model judge. Every number
below is reproducible with the commands in the last section.

## 1. What the runtime actually does

| Module | Responsibility | Reality check |
| --- | --- | --- |
| `assets/registry.py` | load knowledge / usage / skill assets, structural gates | works; validation is structural only |
| `skills/runtime.py` | pick a playbook, execute procedure steps, build traces | deterministic; **never calls a model** |
| `retrieval/*` | keyword / BM25 / semantic-lite / hybrid / TF-IDF / regex | lexical ranking; `semantic` is hashed n-grams, not embeddings |
| `ingestion/compiler.py` | markdown → chunks → claims → concepts → knowledge block | sentence heuristics, fixed confidence 0.55, 24 claims per document |
| `gates/engine.py` | structure, leanness, claim evidence, proposal metadata | claim gate checks only that a quote string is non-empty |
| `evolution/proposal.py` | write-file proposals, apply, rollback | only `write_file` patches; no claim-level delta |
| `kb/` | knowledge and usage assets | 2 knowledge blocks and 5 usage assets against 14 skills |

The single most important fact for this review: the system produces **rendered
templates**, not generated answers. `compose_evidence_answer` ends with
"Use the evidence above as grounded context before drafting a final response."
(`evolvekb/skills/runtime.py:101`). Any claim that EvolveKB answers questions
today is a claim about a template, not about a model.

## 2. Findings

### P0 — integrity

**F1. The headline metrics are tautological.**
`claim_grounding_rate` counts claims whose `evidence_quote` is non-empty
(`evolvekb/demo.py:104`), but the extractor always writes a quote
(`evolvekb/ingestion/compiler.py:104`), so the metric is 1.0 by construction.
`retrieval_vs_playbook_delta` is worse: the retrieval-only arm is hard-coded to
one capability (`evolvekb/evals/runner.py:293`), and the playbook arm is scored by
looking for strings in the rendered template — `"Decision:" in text`
(`evolvekb/evals/runner.py:370`). The published 0.80 delta therefore measures the
template's vocabulary, not behaviour. This directly contradicts the repository's
own honesty rules in `docs/METRICS.md`.

**F2. The claim gate cannot detect a fabricated quote.**
`validate_claim_evidence` only checks `evidence_quote.strip()` is truthy
(`evolvekb/gates/engine.py:57`). Chunks are persisted in `kb/chunks/*.jsonl` and
claims carry `chunk_ids`, so a substring check is available but not implemented.

**F3. Retrieval never sees knowledge bodies.**
`build_lexical_corpus` indexes `name + summary + concepts + tags`
(`evolvekb/retrieval/keyword.py:71`). A block's body text is not searchable, so
detail questions can only match a one-line summary.

### P1 — capability gaps against the stated goal

**F4. The knowledge layer is scaffolding.** 2 knowledge blocks / 5 usage assets vs
14 skills. The repository is a skill-playbook engine with a demo KB, not yet a KB.

**F5. No model in the compile step.** The stated goal is "model 整理知识" with
progressive disclosure; ingestion is deterministic sentence splitting. The only
model-facing artefact is the static `SKILL.md` format.

**F6. No usage learning.** `usage_review.py` aggregates a weekly log, but nothing
turns a successful or failed run into a proposed `UsagePattern`. `usage` assets
are hand-written.

**F7. No "insufficient evidence" state.** `EvidencePack` returns an empty item
list; the playbook still runs and the template still emits an answer. The
evaluation below shows the practical consequence.

### P2 — naming and debt

**F8.** `semantic` is deterministic hashed token/trigram cosine
(`evolvekb/retrieval/semantic.py:56`); the name invites a comparison to embeddings
that the code cannot survive. `docs/RETRIEVAL.md` is honest; the module name is not.

**F9.** `PROC_IMPL` legacy fallback is still live (`evolvekb/skills/runtime.py:202`)
and only produces a warning gate.

## 3. External comparison (2025–2026)

| Route | Representative | Covers | Leaves open | Implication for EvolveKB |
| --- | --- | --- | --- | --- |
| Compiled knowledge / LLM wiki | [Karpathy's llm-wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f); [LLM Wikis as Living Semantic Memory](https://zenodo.org/records/20078453) (preprint) | ingest-time compilation, `index.md`/`log.md`, lint, git versioning | no gates, no rollback protocol | "not RAG" is no longer a differentiator; cite it as shared ground |
| Progressive disclosure | [Anthropic Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) | three-level disclosure, scripts as deterministic tools | static assets; no evolution or evidence layer | SKILL.md as a载体 is occupied; only lifecycle governance is open |
| Evolving playbooks | [ACE: Agentic Context Engineering](https://arxiv.org/abs/2510.04618) | structured bullets with ids and helpful/harmful counters, delta updates, curator dedup, execution feedback | no provenance per bullet, no rollback | closest competitor; EvolveKB must differentiate on governance |
| Agent memory | [Mem0](https://arxiv.org/abs/2504.19413), [Zep/Graphiti](https://arxiv.org/abs/2501.13956) | conflict resolution, bi-temporal validity, invalidation instead of deletion | task procedures rather than conversational facts | borrow the invalidation model for rollback |
| Self-improving agents | [Darwin Gödel Machine](https://arxiv.org/abs/2505.22954), [SICA](https://arxiv.org/abs/2504.15228) | proposal → benchmark validation → archive | changes code, not knowledge; no knowledge-gate semantics | blueprint for "gate = replay" |
| Structured evidence | [RAGFlow / Context as Infrastructure](https://arxiv.org/abs/2610.41172) | claim-evidence leaves, large token savings | reported no accuracy gain on FRAMES; outline degrades with scale | do not claim accuracy wins; claim auditability and cost |

Five judgments that change the positioning:

1. **"Compiled instead of queried" is consensus, not differentiation.** Karpathy's
   idea file and the 2026 preprints already occupy the narrative.
2. **"Playbook decides behaviour" is largely covered by ACE.** The differentiator
   that survives is *governance*: who proposed a change, on which evidence, which
   gate passed, and where the rollback pointer is.
3. **Gate semantics are the real product.** Today gates are structural checks; the
   defensible version is "a knowledge change must pass a replay set", borrowed from
   DGM's archive-and-validate loop.
4. **Evidence sufficiency as an execution precondition is still open.** No surveyed
   system refuses to execute a procedure because evidence is thin.
5. **Accuracy claims will lose.** RAGFlow's own result says compiled artefacts do
   not beat a good harness on accuracy; the honest claims are auditability, token
   cost, and update/rollback behaviour.

## 4. First real-corpus evaluation

Corpus: the repository's own 10 markdown documents (~28 KB), which a pretrained
model is unlikely to have memorised. Ten questions: six lookups, one definition,
one synthesis, one procedure, one unanswerable. One model (`deepseek-flash`) and
one judge model; prompts and questions are in `experiments/real-validation/`.

| System | Mean score (0–2) | Exact | Evidence recall@4 | Unanswerable case |
| --- | --- | --- | --- | --- |
| Long context (all docs) | 1.10 | 10% | 9/9 (trivial) | failed — answered anyway |
| Independent BM25 RAG (top 4 chunks) | **1.40** | **50%** | **8/9** | refused |
| EvolveKB default KB | 0.40 | 10% | n/a (2 blocks) | refused |
| EvolveKB with corpus ingested (9 blocks) | 1.00 | 10% | 4/9 | failed — answered anyway |

What the numbers say:

- **The current KB loses to plain BM25 RAG on its own documentation**, even after
  ingesting it. Retrieval recall@4 is 4/9 against 8/9. The cause is F3: blocks are
  indexed by summary only, so detail questions never reach the body.
- **The default KB cannot answer nine of ten questions** because it contains two
  knowledge blocks. F4 is not a documentation problem, it is the current state.
- **Refusal is accidental.** The populated KB answered the unanswerable question
  because retrieval returned *something*; there is no sufficiency model (F7).
- Long context is not a strong baseline here (1.10): stuffing 35 KB of markdown
  hurts precision, which is consistent with the retrieval literature.

Limits: one corpus, ten questions, one model, one run, LLM judge without blind
human review. The corpus is the project's own documentation, so questions are
about EvolveKB rather than an external domain. These numbers are a signal, not a
benchmark.

## 5. Proposed next iteration

| Priority | Change | Acceptance |
| --- | --- | --- |
| P0 | Gate verifies `evidence_quote` is a substring of the referenced chunk; add a fixture with a fabricated quote that must fail | fabricated-quote fixture fails the gate; all real claims pass |
| P0 | Replace tautological metrics: the retrieval-only arm must actually run; playbook capabilities are checked on artifacts (JSON schema), not template strings | the delta can go down when the playbook is degraded; a test forces that |
| P0 | Index chunk bodies and emit chunk-level evidence with `chunk_ids` | evidence recall@4 ≥ the independent BM25 baseline on this corpus |
| P0 | Add `insufficient_evidence` to `EvidencePack`; playbooks branch on it | the unanswerable question is refused, not answered |
| P1 | Optional model compiler: claims must carry verified quote offsets; deterministic path stays the default | every model-written claim passes the offset check |
| P1 | Usage learning: post-hoc attribution → `UsagePattern` proposal → replay gate | a pattern can be proposed, gated, applied, and rolled back |
| P1 | Claim-level delta operations (add / supersede / invalidate) | no whole-file rewrite in proposals |
| P2 | External corpus + update/rollback and playbook-ablation experiments | reproducible report with stale-contamination and pass^k |

The order matters: F1 and F2 must be fixed before any new number is published,
otherwise the project repeats the mistake this review is criticising.

## 7. Update — metric integrity and reliability (2026-11-27)

Issue #19 is fixed in [PR #21](https://github.com/2sao7sao/EvolveKB/pull/21).

- `claim_grounding_rate` now requires the quote to appear in its source chunk, so a fabricated quote lowers it.
- `retrieval_vs_playbook_delta` now runs both arms, turns each into an artefact, and scores both with the same checker. The demo delta moves from a definitional **0.80** to a measured **0.60** (retrieval arm 2/5, playbook 5/5), and a degraded playbook lowers it further (test enforced).

Reliability over repeated samples (`experiments/reliability/`): 10 questions, **5 samples each** at temperature 0.8, pass means judge score 2.

| System | pass@1 | pass@5 | pass^5 | mean score |
| --- | --- | --- | --- | --- |
| Independent BM25 RAG | **0.28** | **0.50** | **0.10** | **1.20** |
| EvolveKB with ingested KB | 0.16 | 0.30 | **0.00** | 0.96 |

Reading: the KB's occasional correct answer is not a stable capability. It never answers any question correctly in all five samples, while with more attempts BM25 reaches 0.50 — the gap widens with k, which is what you expect when the bottleneck is evidence quality rather than sampling noise. That points back to F3 (retrieval indexes summaries, not bodies) and to issue #20.
## 6. Reproduction

```bash
python -m evolvekb.cli eval run "evals/*.yaml"          # seed suites
python -m evolvekb.cli demo                              # demo metrics
python experiments/real-validation/run_benchmark.py       # the pilot above
python experiments/real-validation/analyze_recall.py      # recall@4
```

The pilot calls `deepseek-flash` with the key at `~/.config/evolve-memory/deepseek.key`
and writes results under `experiments/real-validation/results/`.
