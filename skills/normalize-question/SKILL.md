---
name: normalize-question
description: Normalize a user question into a structured object (targets, constraints, intent_hint). Used as a first step in most playbooks.
metadata:
  kind: procedure
  inputs:
    question: str
  outputs:
    norm: dict
---

# normalize-question (procedure)

## Contract
**Input**: `question: str`  
**Output**: `norm: { intent_hint, targets, constraints, raw }`

## Deterministic MVP behavior
- Extract rough targets via substring matching
- Set `intent_hint` to `compare_frameworks` if question contains comparison-like terms
