---
schema_version: 2
name: compare-frameworks
description: Compare two frameworks or approaches using a stable, execution-first playbook.
allowed-tools: []
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
  preconditions:
    - question must describe two or more approaches to compare
  postconditions:
    - outputs.answer_md must include a comparison table and tradeoffs
  version: 0.2.0
---

# compare-frameworks (playbook)

This skill is a playbook. Execution engine reads the frontmatter steps.
