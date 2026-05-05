---
schema_version: 2
name: compose-evidence-answer
description: Compose a markdown answer from a user question and retrieved evidence pack.
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
    - answer_md must include evidence references
  version: 0.2.0
---

# compose-evidence-answer (procedure)

Render retrieved evidence before drafting the final answer.
