---
schema_version: 2
id: usage_compare_frameworks
name: compare-frameworks
kind: usage
uses:
- graphrag-core
- execution-first-kb
intent: compare_frameworks
strategy: playbook
pattern: required
playbook: compare-frameworks
steps:
- normalize-question
- build-comparison-axes
- contrast-matrix
- compose-answer-md
trigger_examples:
- Compare GraphRAG and execution-first KB
- 对比两个技术框架
anti_trigger_examples:
- 帮我总结这篇文章
gate_policy_ids: []
eval_case_ids: []
updated_at: 2026-05-01
needs_review: false
---

# compare-frameworks

Auto-generated usage plan.
