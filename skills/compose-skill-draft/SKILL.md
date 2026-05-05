---
schema_version: 2
name: compose-skill-draft
description: Compose a SKILL.md draft from an extracted outline.
allowed-tools: []
metadata:
  kind: procedure
  inputs:
    outline: dict
  outputs:
    skill_md: str
  preconditions:
    - outline must include doc_name or headings
  postconditions:
    - output must be valid markdown
  version: 0.2.0
---

# compose-skill-draft (procedure)

Create a minimal SKILL.md from the outline.
