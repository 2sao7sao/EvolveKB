---
schema_version: 2
name: compose-knowledge-md
description: Compose a knowledge asset markdown from an extracted outline.
allowed-tools: []
metadata:
  kind: procedure
  inputs:
    outline: dict
  outputs:
    knowledge_md: str
  preconditions:
    - outline must include doc_name and doc_path
  postconditions:
    - knowledge_md must include schema_version 2 frontmatter
  version: 0.2.0
---

# compose-knowledge-md (procedure)

Create a minimal knowledge markdown block.
