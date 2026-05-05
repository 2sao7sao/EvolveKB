---
schema_version: 2
id: usage_answer_with_evidence
name: answer-with-evidence
kind: usage
intent: answer_with_evidence
strategy: playbook
pattern: optional
uses:
- graphrag-core
- execution-first-kb
playbook: answer-with-evidence
steps:
- retrieve-evidence
- compose-evidence-answer
trigger_examples:
- Answer using current KB evidence
- 用当前知识库证据回答这个问题
anti_trigger_examples:
- Create a new long-form source document
gate_policy_ids: []
eval_case_ids:
- eval_retrieval_execution_first_001
updated_at: 2026-05-05
needs_review: false
---

# answer-with-evidence

Use this when a query should be grounded in current KB assets before response composition.
