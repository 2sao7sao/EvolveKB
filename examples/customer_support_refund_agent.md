# Customer Support Refund Agent

This example shows EvolveKB as an execution-first support workflow, not a
retrieval-only Q&A script.

## Scenario

A customer asks whether they can get a refund for an opened item after 45 days.
The agent must cite policy evidence, run the refund decision playbook, produce a
decision, run gates, and show a trace id.

## Run

```bash
python examples/customer_support_refund_agent.py
```

The script runs in an isolated temporary workspace and does not modify your
checkout.

## Expected Shape

```text
# Customer Support Refund Agent Demo

1. Load policy document
2. Compile grounded claims
3. Build / load refund decision playbook
4. Retrieve evidence for customer question
5. Run playbook steps
6. Produce evidence-backed answer
7. Run gates and evals
8. Show trace id and proposal path
```

The answer includes:

- `Decision: needs_review`
- evidence ids
- source refs
- a trace id
- a proposal path generated during policy compilation
