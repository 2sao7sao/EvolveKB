---
schema_version: 2
name: retrieve-evidence
description: Retrieve evidence-backed knowledge and claims for a user query before composing an answer.
allowed-tools: [Read]
metadata:
  kind: procedure
  inputs:
    query: str
    limit: int
  outputs:
    evidence: dict
  preconditions:
    - query must be a non-empty string
  postconditions:
    - evidence must include citations and retrieved evidence items
  runtime:
    type: python
    entrypoint: evolvekb.procedures.retrieve_evidence:run
    timeout_ms: 3000
    side_effects: false
  version: 0.3.0
---

# retrieve-evidence (procedure)

Use keyword retrieval over `kb/knowledge` and compiled `kb/claims` as evidence supply.
