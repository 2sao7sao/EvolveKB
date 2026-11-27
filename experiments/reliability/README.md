# Reliability: pass@1 and pass@k

The real-corpus pilot answers each question once. This directory samples the same
questions several times per system, so a single lucky answer cannot stand in for
reliability.

## Definitions

- **pass@1**: mean over questions of `passes / samples` — the chance a single
  answer is fully correct.
- **pass@k**: the unbiased estimator `1 - C(n-c, k) / C(n, k)` averaged over
  questions — the chance at least one of k answers is fully correct.
- **pass^k**: `C(c, k) / C(n, k)` averaged over questions — the chance that all
  k answers are fully correct, i.e. reliability under repetition.

A sample counts as a pass only when the judge returns score 2 (fully correct and
free of fabricated facts).

## Run

```bash
EVOLVEKB_KB_ROOT=/tmp/evolvekb-kb python experiments/reliability/run_reliability.py \
  --samples 5 --systems bm25_rag,kb_evidence
```

`EVOLVEKB_KB_ROOT` points at a copy of the repository with the corpus ingested
(`python -m evolvekb.cli ingest <doc>` for each document). Without it the KB arm
has almost no evidence to return, which the pilot already showed.

## Limits

- 10 questions and 5 samples: pass@k is coarse; k > 5 is not estimated.
- The judge is another model call, not a human; a wrong answer that convinces the
  judge counts as a pass.
- Answers are sampled at temperature 0.8 from `deepseek-flash`; results will move
  with model, prompt, and corpus.
