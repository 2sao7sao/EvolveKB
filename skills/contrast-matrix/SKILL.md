---
name: contrast-matrix
description: Create a structured comparison matrix (axis, A, B, tradeoff) from axes and normalized question.
metadata:
  kind: procedure
  inputs:
    norm: dict
    axes: list
  outputs:
    matrix: list
---

# contrast-matrix (procedure)

Fill the matrix. Use "unknown" when missing evidence; do not invent hard facts.
