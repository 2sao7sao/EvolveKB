---
schema_version: 2
name: answer-with-evidence
description: Answer a question by retrieving evidence first, then composing a grounded markdown answer.
allowed-tools: []
metadata:
  kind: playbook
  intent: answer_with_evidence
  steps:
    - call: retrieve-evidence
      in:
        query: $inputs.question
        limit: 5
      out: $ctx.evidence
    - call: compose-evidence-answer
      in:
        question: $inputs.question
        evidence: $ctx.evidence
      out: $outputs.answer_md
  preconditions:
    - question must be answerable from current KB evidence
  postconditions:
    - outputs.answer_md must include evidence references
  version: 0.2.0
---

# answer-with-evidence (playbook)

This playbook keeps retrieval as evidence supply while preserving execution-first routing.
