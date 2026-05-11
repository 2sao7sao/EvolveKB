# EvolveKB Flagship Demo

This is the product path the README points to. It is intentionally small and
deterministic so a developer can inspect every artifact instead of trusting a
black-box model run.

## Scenario

A support team has a refund policy. A retrieval-only system can find the refund
paragraph. EvolveKB should turn the policy into a governed agent capability:

```text
refund_policy.md
  -> claims with evidence
  -> knowledge proposal
  -> validation gates
  -> regression evals
  -> pending review
```

The demo does not claim that keyword retrieval beats RAG. It shows the extra
engineering surface an agent needs when knowledge must drive behavior.

## Run It

```bash
python -m evolvekb.cli demo
```

or:

```bash
python examples/run_evolution_loop.py
```

Both commands run in an isolated temporary workspace and leave the source repo
unchanged.

## Expected Output Shape

```text
# EvolveKB Flagship Demo

status: PASS
source_doc: examples/refund_policy.md

## 1. Ingest policy into knowledge assets
- claims: 5
- grounded_claims: 5
- proposal: kb/proposals/...

## 2. Run gates and regression evals
- gates: PASS (0 blocking failures)
- evals: 2/2 passed
- pending_proposals: 1

## 3. Product metrics
- claim_grounding_rate: 1.00 (5/5)
- playbook_success_rate: 1.00 (2/2)
- proposal_gate_pass_rate: 1.00 (1/1)
- retrieval_vs_playbook_delta: 0.80 (4/5)
```

## What Each Metric Means

| Metric | Definition | Why it matters |
| --- | --- | --- |
| `claim_grounding_rate` | Share of extracted claims that retain source evidence. | Prevents unsourced knowledge from becoming agent behavior. |
| `playbook_success_rate` | Share of seed evals passed by routing/retrieval runtime. | Shows the current runtime path is executable. |
| `proposal_gate_pass_rate` | Whether proposal creation keeps gates green. | Knowledge changes should be reviewable before acceptance. |
| `retrieval_vs_playbook_delta` | Capability coverage gained beyond retrieval-only baseline. | Makes the RAG-vs-runtime distinction explicit. |

The current delta is capability coverage, not model accuracy. The retrieval-only
baseline can retrieve relevant policy text. The execution-first path also
extracts grounded claims, runs gates, runs evals, and creates a reviewable
proposal.

## Artifacts Created During The Demo

| Artifact | Meaning |
| --- | --- |
| `kb/sources/*.json` | Source document metadata and content hash. |
| `kb/chunks/*.jsonl` | Deterministic markdown chunks. |
| `kb/claims/*.jsonl` | Extracted claims with source evidence quotes. |
| `kb/concepts/*.jsonl` | Lightweight concepts linked to claims. |
| `kb/proposals/*.md` | Pending knowledge update proposal. |

## What To Improve Next

| Area | Next step |
| --- | --- |
| Retrieval baseline | Add semantic and hybrid retriever baselines behind the same evidence contract. |
| Eval breadth | Add real support, compliance, engineering, and ops knowledge tasks. |
| Skill execution | Add domain-specific playbooks that consume the generated policy proposal. |
| Governance | Add approval metadata and reviewer decisions to proposal lifecycle. |
