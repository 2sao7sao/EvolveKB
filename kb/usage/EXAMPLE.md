---
schema_version: 2
id: usage_compare_frameworks_example
name: compare-frameworks-example
kind: usage
intent: compare_frameworks
strategy: playbook
pattern: required
uses: [graphrag-core, execution-first-kb]
playbook: compare-frameworks
steps:
  - normalize-question
  - build-comparison-axes
  - contrast-matrix
  - compose-answer-md
trigger_examples:
  - Compare GraphRAG and execution-first KB
anti_trigger_examples:
  - Summarize this article
gate_policy_ids: []
eval_case_ids: []
updated_at: 2026-03-04
needs_review: false
---

# Compare Frameworks

Usage logic referencing knowledge assets.
