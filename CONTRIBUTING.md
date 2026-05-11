# Contributing to EvolveKB

EvolveKB is an execution-first knowledge runtime. Contributions should make
knowledge easier to use, verify, evolve, or integrate into agent harnesses.

## Development Setup

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
python -m evolvekb.cli validate --settings settings/evolve.yaml
python -m evolvekb.cli eval run "evals/*.yaml"
```

Run the flagship demo:

```bash
python examples/run_evolution_loop.py
```

## Good Contributions

| Area | Examples |
| --- | --- |
| Knowledge evolution | Better proposal review, rollback metadata, regression guards. |
| Skills | Stronger `SKILL.md` contracts, clearer examples, failure-mode tests. |
| Evals | RAG baseline comparisons, evidence grounding, playbook success metrics. |
| Integrations | Harness examples for single-agent and multi-agent workflows. |
| Documentation | Shorter quickstarts, before/after examples, diagrams with clear labels. |

## Quality Bar

- Add tests for behavior changes.
- Keep examples runnable without private credentials.
- Do not commit API keys, raw private traces, customer data, or proprietary docs.
- Prefer deterministic fixtures before adding model-graded evals.
- Clearly distinguish prototype signals from benchmark claims.

## Pull Request Checklist

- `python -m pytest -q` passes.
- `python -m evolvekb.cli validate --settings settings/evolve.yaml` passes.
- Relevant README, examples, or schema docs are updated.
- New knowledge assets include evidence and usage context.
