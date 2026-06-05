# Contributing to EvolveKB

EvolveKB is an execution-first knowledge runtime. Contributions should make
agent knowledge easier to execute, verify, review, or evolve safely.

## What Kind Of Project Is This?

EvolveKB is not trying to be a better keyword retriever. The retrieval layer is
currently a deterministic baseline. The core project is the governed runtime
around agent knowledge:

| Layer | What contributors improve |
| --- | --- |
| Knowledge assets | Claims, evidence, concepts, and source links. |
| Usage assets | When knowledge should be used and what behavior it should trigger. |
| Skills | Repeatable `SKILL.md` procedures and playbooks. |
| Gates | Validation rules that keep knowledge changes reviewable. |
| Evals | Regression seeds for retrieval, routing, evidence use, and playbook behavior. |
| Governance | Proposals, review metadata, rollback paths, and auditability. |

## Good First Contributions

Start with changes that are deterministic and easy to review.

| Area | Examples |
| --- | --- |
| Docs | Clarify a README section, add a short walkthrough, improve a diagram caption. |
| Skills | Add a failure mode, tighten preconditions, or document expected outputs. |
| Evals | Add one seed case for retrieval, routing, or missing evidence. |
| Gates | Add a focused validation error with a matching test. |
| Demo | Improve provenance docs or make a metric explanation easier to audit. |

## Pick Your First PR

| Starter PR | Why it helps | Where to start |
| --- | --- | --- |
| Add a missing-evidence eval seed | Prevents unsupported answers from becoming accepted behavior. | `evals/`, `tests/` |
| Improve a skill failure-mode section | Makes `SKILL.md` procedures safer to call from agent harnesses. | `skills/*/SKILL.md` |
| Add a rollback lifecycle test | Strengthens the governed update path. | `tests/test_phase2_foundation.py` |
| Expand retrieval baseline notes | Keeps prototype claims honest. | `README.md`, `docs/METRICS.md` |
| Improve issue template examples | Helps contributors file actionable work. | `.github/ISSUE_TEMPLATE/` |

More options live in [docs/STARTER_ISSUES.md](docs/STARTER_ISSUES.md).

## Local Setup

```bash
git clone https://github.com/2sao7sao/EvolveKB.git
cd EvolveKB
python -m pip install -e ".[dev]"
```

Run the flagship demo:

```bash
python -m evolvekb.cli demo
```

## Run Quality Checks

Use these before opening a PR:

```bash
python -m pytest -q
python -m evolvekb.cli validate --settings settings/evolve.yaml
python -m evolvekb.cli eval run "evals/*.yaml"
```

For targeted skill work:

```bash
python -m evolvekb.cli skills inspect compare-frameworks
```

## Add A New SKILL.md Procedure

1. Copy [docs/SKILL_TEMPLATE.md](docs/SKILL_TEMPLATE.md) into
   `skills/<new-skill>/SKILL.md`.
2. Use `metadata.kind: procedure`.
3. Declare inputs, outputs, preconditions, postconditions, and failure modes.
4. Prefer existing procedure calls in `metadata.steps` before adding new ones.
5. Run `python -m evolvekb.cli validate --settings settings/evolve.yaml`.

Procedures should be small, deterministic, and inspectable. Do not hide broad
agent behavior behind vague prose.

## Add A Playbook

1. Use `metadata.kind: playbook`.
2. Add `metadata.intent` so `PlaybookRuntime` can route to it.
3. Reference procedure steps by name.
4. Add or update a usage asset in `kb/usage/` when the playbook changes how
   knowledge is applied.
5. Add a routing eval under `evals/` if runtime selection behavior changes.

## Add A Retrieval Or Eval Case

| Case type | Expected shape |
| --- | --- |
| Retrieval eval | Query plus `expected.must_retrieve` targets. |
| Routing eval | Input intent plus expected selected playbook. |
| Capability coverage eval | Minimum demo metrics and required gates/proposals. |

Keep evals deterministic. If a future PR introduces model-graded evals, mark the
scope, model dependency, and flake risk explicitly.

## Documentation

Update docs whenever behavior, claims, or contributor workflows change.

| Change | Docs to check |
| --- | --- |
| Demo metrics | `README.md`, `README.zh.md`, `docs/METRICS.md` |
| New skill pattern | `docs/SKILL_TEMPLATE.md`, relevant `skills/*/SKILL.md` |
| Contributor entry points | `CONTRIBUTING.md`, `docs/STARTER_ISSUES.md` |
| README image changes | `docs/assets/README.md`, `docs/assets/evolvekb-demo-terminal.svg` |

## Prototype Vs Benchmark Claims

Be precise about evidence:

| Claim type | Requirement |
| --- | --- |
| Prototype signal | State the seed, fixture, or local command that supports it. |
| Benchmark claim | Include dataset, baseline, scoring method, and reproducible command. |
| Retrieval comparison | Separate retrieval quality from governed knowledge-use capability. |
| Product metric | Include numerator, denominator, and source artifact. |

Do not claim that the current keyword retriever beats semantic or hybrid
retrieval. The current `retrieval_vs_playbook_delta` measures seed-level
capability coverage beyond retrieval-only behavior.

## Security Rules

- Do not commit API keys, tokens, private documents, customer traces, or
  proprietary run outputs.
- Do not add autonomous write paths without explicit review gates.
- Keep examples runnable without private credentials.
- Redact sensitive data from proposals, logs, screenshots, and README imagery.
- Prefer deterministic fixtures over real customer data.

## Pull Request Checklist

- The PR has one clear purpose.
- Behavior changes include focused tests or evals.
- `python -m pytest -q` passes.
- `python -m evolvekb.cli validate --settings settings/evolve.yaml` passes.
- `python -m evolvekb.cli eval run "evals/*.yaml"` passes when eval behavior is touched.
- README, docs, templates, or examples are updated when public behavior changes.
- Prototype signals and benchmark claims are labeled honestly.
