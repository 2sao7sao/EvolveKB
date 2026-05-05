---
schema_version: 2
name: build-comparison-axes
description: Build 5-8 comparison axes for comparing two technical frameworks. Used in compare playbooks.
allowed-tools: []
metadata:
  kind: procedure
  inputs:
    norm: dict
  outputs:
    axes: list
  preconditions:
    - norm must include raw question text
  postconditions:
    - axes must be a non-empty list
  version: 0.2.0
---

# build-comparison-axes (procedure)

Generate axes such as:
- index_time_synthesis
- query_time_cost
- governance
- multi_hop
- maintenance
