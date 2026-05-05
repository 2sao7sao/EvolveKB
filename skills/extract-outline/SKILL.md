---
schema_version: 2
name: extract-outline
description: Extract headings and a short summary from a markdown document.
allowed-tools: [Read]
metadata:
  kind: procedure
  inputs:
    doc_path: str
  outputs:
    outline: list
    summary: str
    doc_name: str
    doc_path: str
  preconditions:
    - doc_path must exist
  postconditions:
    - output must include headings and source path
  version: 0.2.0
---

# extract-outline (procedure)

Parse headings and produce a brief summary from the document.
