# Metrics

EvolveKB demo metrics are computed from runtime artifacts. They are meant to make
the current product path auditable, not to claim broad retrieval superiority.

Run them with:

```bash
python -m evolvekb.cli demo
python -m evolvekb.cli eval run "evals/*.yaml"
```

## Demo Metrics

| Metric | Formula | Current seed output |
| --- | --- | --- |
| `claim_grounding_rate` | `grounded_claim_count / claim_count` | `5/5 = 1.00` |
| `playbook_success_rate` | `passed_eval_count / eval_count` | `2/2 = 1.00` |
| `proposal_gate_pass_rate` | `1` when a proposal is created and gates pass, else `0` | `1/1 = 1.00` |
| `retrieval_vs_playbook_delta` | `playbook_capability_coverage - retrieval_only_capability_coverage` | `4/5 = 0.80` |

The CLI prints each metric with its numerator and denominator so README numbers
can be checked against a local run.

## Retrieval Vs Playbook Delta

This metric answers one narrow seed-level question:

> How many required agent-knowledge capabilities does the execution-first path
> cover beyond a retrieval-only baseline?

The implementation lives in `evolvekb.demo.CAPABILITY_COVERAGE_CHECKLIST`.

```text
delta =
  (playbook_capability_coverage - retrieval_only_capability_coverage)

coverage =
  passed_capabilities / total_required_capabilities
```

Current checklist:

| Capability | Retrieval-only baseline | Execution-first playbook |
| --- | --- | --- |
| Finds relevant policy text | yes | yes |
| Produces evidence-backed claims | no | yes |
| Routes to an explicit usage playbook | no | yes |
| Runs repeatable procedure steps | no | yes |
| Creates a reviewable proposal and gates | no | yes |

Current seed calculation:

```text
retrieval_only_capability_coverage = 1 / 5
playbook_capability_coverage = 5 / 5
retrieval_vs_playbook_delta = 5/5 - 1/5 = 4/5 = 0.80
```

## Scope

These metrics are intentionally small. They validate the repo's executable
product path:

- ingest a synthetic policy document
- preserve claim evidence
- route through seed evals
- run validation gates
- produce a reviewable proposal

They do not prove that keyword retrieval beats semantic retrieval, that the
runtime is production-ready for every domain, or that the current eval set is a
comprehensive benchmark.
