---
schema_version: 2
name: normalize-question
description: Normalize a user question into a structured object (targets, constraints, intent_hint). Used as a first step in most playbooks.
allowed-tools: []
metadata:
  kind: procedure
  inputs:
    question: str
  outputs:
    norm: dict
  preconditions:
    - question must be a string
  postconditions:
    - norm must include intent_hint, targets, constraints, and raw
  version: 0.2.0
---

# normalize-question (procedure)

## Contract
**Input**: `question: str`  
**Output**: `norm: { intent_hint, targets, constraints, raw }`

## Deterministic MVP behavior
- Extract rough targets via substring matching
- Set `intent_hint` to `compare_frameworks` if question contains comparison-like terms
