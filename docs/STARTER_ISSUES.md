# Starter Issues

These issues are intentionally scoped for first-time contributors. Each one
should fit in a small PR with docs or focused tests.

| Issue | Good first outcome | Suggested files |
| --- | --- | --- |
| Document a new failure mode for `answer-with-evidence` | Add a short failure-mode section and one validation expectation. | `skills/answer-with-evidence/SKILL.md`, `tests/test_phase2_foundation.py` |
| Add an eval seed for missing evidence | Create a small YAML eval that verifies the runtime does not invent evidence. | `evals/`, `evolvekb/evals/runner.py` if a new category is needed |
| Improve the demo asset refresh instructions | Add a command transcript or screenshot refresh note without changing runtime behavior. | `docs/assets/README.md` |
| Add a contributor example for a procedure skill | Create a tiny docs-only walkthrough using `docs/SKILL_TEMPLATE.md`. | `docs/`, `CONTRIBUTING.md` |
| Expand retrieval baseline notes | Explain the current keyword retriever limits and candidate semantic/hybrid interfaces. | `README.md`, `docs/METRICS.md` |
| Add a rollback lifecycle test | Cover one more proposal rollback edge case with deterministic fixtures. | `tests/test_phase2_foundation.py`, `evolvekb/evolution/` |
| Improve issue template examples | Add clearer placeholder examples for bug reports, skill PRs, or eval case requests. | `.github/ISSUE_TEMPLATE/` |

## First PR Checklist

- Keep the PR focused on one issue.
- Add or update tests when behavior changes.
- Run `python -m pytest -q`.
- Run `python -m evolvekb.cli validate --settings settings/evolve.yaml`.
- Avoid private documents, private traces, credentials, and generated proposal
  output containing sensitive data.
