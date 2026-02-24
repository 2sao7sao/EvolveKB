---
name: compare-frameworks
description: Compare two frameworks/approaches using a stable, execution-first playbook (no retrieval).
metadata:
  kind: playbook
  intent: compare_frameworks
  steps:
    - call: normalize-question
      in:
        question: $inputs.question
      out: $ctx.norm
    - call: build-comparison-axes
      in:
        norm: $ctx.norm
      out: $ctx.axes
    - call: contrast-matrix
      in:
        norm: $ctx.norm
        axes: $ctx.axes
      out: $ctx.matrix
    - call: compose-answer-md
      in:
        norm: $ctx.norm
        matrix: $ctx.matrix
      out: $outputs.answer_md
---

# compare-frameworks (playbook)

This skill is a playbook. Execution engine reads the frontmatter steps.
