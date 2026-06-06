---
schema_version: 2
id: usage_refund_decision
name: refund-decision
kind: usage
intent: refund_decision
strategy: playbook
pattern: required
uses:
  - execution-first-kb
playbook: refund-decision
steps:
  - retrieve policy evidence
  - decide refund status
  - cite evidence ids and source refs
trigger_examples:
  - "Can the customer get a refund after opening the item?"
  - "Should this support ticket be escalated for refund approval?"
anti_trigger_examples:
  - "Summarize all refund policies without making a decision."
gate_policy_ids: []
eval_case_ids:
  - eval_playbook_refund_decision_001
updated_at: 2026-06-05
needs_review: false
---

# refund-decision

Use the `refund-decision` playbook when a customer refund request requires a
policy-backed decision with cited evidence.
