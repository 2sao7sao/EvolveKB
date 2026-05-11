# EvolveKB Flagship Demo: From Static Policy to Verified Agent Skill

This demo describes the product path EvolveKB should make obvious in the README.
It is intentionally small: a user should understand the difference from plain RAG
without reading the whole codebase.

## Scenario

A support team has a refund policy document. A normal RAG system can retrieve
the refund paragraph. EvolveKB should turn the policy into an executable agent
procedure and keep it safe to evolve.

```text
policy.md
  -> claims with evidence
  -> knowledge asset
  -> usage playbook for "refund eligibility"
  -> SKILL.md procedure
  -> gate validation
  -> eval cases
  -> proposal when practice exposes a gap
```

## What Good Looks Like

| Step | Expected product behavior | Why it matters |
| --- | --- | --- |
| Ingest | Extract policy claims, source references, eligibility rules, and exceptions. | Knowledge becomes inspectable instead of raw chunks. |
| Organize | Link claims to a usage asset such as `support_refund_decision`. | The system knows how the knowledge is supposed to be used. |
| Execute | Route a refund request to a procedural skill. | The agent performs a repeatable workflow, not free-form guessing. |
| Verify | Run gates for evidence, forbidden claims, approval requirements, and eval cases. | Knowledge updates cannot silently break production behavior. |
| Evolve | When a refund case fails, propose a reviewed knowledge/playbook update. | Practice changes the knowledge base through an auditable loop. |

## Minimal Commands

```bash
python examples/run_evolution_loop.py
```

The script copies the repository to a temporary workspace, ingests
`examples/refund_policy.md`, runs gates and evals, and lists the generated
proposal without changing your working tree.

## Metrics to Add Next

| Metric | Definition |
| --- | --- |
| `claim_grounding_rate` | Share of extracted claims backed by source evidence. |
| `usage_playbook_success_rate` | Share of tasks completed through the intended playbook. |
| `hidden_dependency_discovery` | Whether cross-document constraints are discovered and linked. |
| `proposal_acceptance_rate` | Share of generated updates that pass gates and human review. |
| `rag_delta` | Task-success delta between plain retrieval and EvolveKB playbook execution. |

## Positioning

Plain RAG asks: "Which chunks are similar to the query?"

EvolveKB asks: "What should the agent do with this knowledge, how do we verify
that behavior, and how does practice update the knowledge safely?"
