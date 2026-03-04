---
name: ingest-doc
description: Ingest a markdown document and draft a procedure skill.
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
---

# ingest-doc (playbook)

Generate a skill draft from a document path.
