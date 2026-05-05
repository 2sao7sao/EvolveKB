---
schema_version: 2
kind: kb-index
updated_at: 2026-05-05
---

# EvolveKB Index

## Knowledge
- [[knowledge/execution-first-kb]] — Execution-first knowledge turns reusable knowledge logic into playbooks, procedures, settings, and gates instead of relying only on retrieved text chunks. _(concepts: execution-first, playbook, procedure, gate, knowledge-runtime)_
- [[knowledge/graphrag-core]] — GraphRAG builds a graph of entities/relations and uses it to connect evidence during retrieval. _(concepts: entity-linking, graph-traversal, community-summarization)_

## Usage
- [[usage/answer-with-evidence]] — intent `answer_with_evidence`, pattern `optional`, uses: graphrag-core, execution-first-kb
- [[usage/compare-frameworks]] — intent `compare_frameworks`, pattern `required`, uses: graphrag-core, execution-first-kb
- [[usage/compare-frameworks-example]] — intent `compare_frameworks`, pattern `required`, uses: graphrag-core, execution-first-kb

## Skills
- [[../skills/answer-with-evidence/SKILL]] — `playbook`, intent `answer_with_evidence`, version `0.2.0`
- [[../skills/build-comparison-axes/SKILL]] — `procedure`, version `0.2.0`
- [[../skills/compare-frameworks/SKILL]] — `playbook`, intent `compare_frameworks`, version `0.2.0`
- [[../skills/compose-answer-md/SKILL]] — `procedure`, version `0.2.0`
- [[../skills/compose-evidence-answer/SKILL]] — `procedure`, version `0.2.0`
- [[../skills/compose-knowledge-md/SKILL]] — `procedure`, version `0.2.0`
- [[../skills/compose-skill-draft/SKILL]] — `procedure`, version `0.2.0`
- [[../skills/contrast-matrix/SKILL]] — `procedure`, version `0.2.0`
- [[../skills/extract-outline/SKILL]] — `procedure`, version `0.2.0`
- [[../skills/ingest-doc/SKILL]] — `playbook`, intent `ingest_doc`, version `0.2.0`
- [[../skills/normalize-question/SKILL]] — `procedure`, version `0.2.0`
- [[../skills/retrieve-evidence/SKILL]] — `procedure`, version `0.2.0`
