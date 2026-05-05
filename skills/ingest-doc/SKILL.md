---
schema_version: 2
name: ingest-doc
description: Ingest a markdown document and draft a procedure skill.
allowed-tools: []
metadata:
  kind: playbook
  intent: ingest_doc
  steps:
    - call: extract-outline
      in:
        doc_path: $inputs.doc_path
      out: $ctx.outline
    - call: compose-knowledge-md
      in:
        outline: $ctx.outline
      out: $outputs.knowledge_md
  preconditions:
    - doc_path must point to a readable markdown file
  postconditions:
    - outputs.knowledge_md must include knowledge frontmatter
  version: 0.2.0
---

# ingest-doc (playbook)

Generate a skill draft from a document path.
