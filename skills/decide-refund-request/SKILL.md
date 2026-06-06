---
schema_version: 2
name: decide-refund-request
description: Decide a customer refund request from a grounded evidence pack.
allowed-tools: []
metadata:
  kind: procedure
  inputs:
    question: str
    evidence: dict
  outputs:
    answer_md: str
  preconditions:
    - evidence must come from retrieve-evidence
  postconditions:
    - answer_md must include a decision, evidence ids, and source refs
  runtime:
    type: python
    entrypoint: evolvekb.procedures.refund_decision:run
    timeout_ms: 3000
    side_effects: false
  version: 0.3.0
---

# decide-refund-request (procedure)

Return `eligible`, `not_eligible`, or `needs_review` with cited evidence.
