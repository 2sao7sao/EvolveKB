---
schema_version: 2
name: refund-decision
description: Route a customer refund question through evidence retrieval and a policy-backed decision step.
allowed-tools: []
metadata:
  kind: playbook
  intent: refund_decision
  steps:
    - call: retrieve-evidence
      in:
        query: $inputs.question
        limit: 5
      out: $ctx.evidence
    - call: decide-refund-request
      in:
        question: $inputs.question
        evidence: $ctx.evidence
      out: $outputs.answer_md
  preconditions:
    - question must describe a customer refund request
  postconditions:
    - outputs.answer_md must include evidence ids and source refs
  version: 0.3.0
---

# refund-decision (playbook)

Use this playbook when a support agent must answer a refund request with policy evidence.
