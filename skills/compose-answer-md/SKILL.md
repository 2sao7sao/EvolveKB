---
schema_version: 2
name: compose-answer-md
description: Render a markdown answer from a comparison matrix.
allowed-tools: []
metadata:
  kind: procedure
  inputs:
    norm: dict
    matrix: list
  outputs:
    answer_md: str
  preconditions:
    - matrix must contain comparison rows
  postconditions:
    - answer_md must be markdown
  version: 0.2.0
---

# compose-answer-md (procedure)

Return a well-structured markdown answer.
