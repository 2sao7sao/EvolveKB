---
schema_version: 2
name: contrast-matrix
description: Create a structured comparison matrix (axis, A, B, tradeoff) from axes and normalized question.
allowed-tools: []
metadata:
  kind: procedure
  inputs:
    norm: dict
    axes: list
  outputs:
    matrix: list
  preconditions:
    - axes must be present
  postconditions:
    - matrix rows must include axis, A, B, and tradeoff
  version: 0.2.0
---

# contrast-matrix (procedure)

Fill the matrix. Use "unknown" when missing evidence; do not invent hard facts.
