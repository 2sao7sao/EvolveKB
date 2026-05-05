# Knowledge Base Schema v2

This folder separates knowledge assets and usage assets.

## knowledge/

Stores distilled, model‑understood knowledge.

Required frontmatter:

```yaml
---
schema_version: 2
id: kb_example
name: <kebab-name>
kind: knowledge
block_type: concept | pattern | decision | procedure | case | reference
source_refs:
  - source_id: <path or source id>
    chunk_ids: []
summary: <one paragraph>
claims: []
concepts: [list, of, concepts]
confidence: 0.0..1.0
recommended_usage: []
tags: []
updated_at: YYYY-MM-DD
version: 1
status: active | conflicting | superseded | rejected
---
```

## usage/

Stores how to use knowledge (playbooks / procedures / strategies).

Required frontmatter:

```yaml
---
schema_version: 2
id: usage_example
name: <kebab-name>
kind: usage
uses: [knowledge-name-1, knowledge-name-2]
intent: <intent-name>
strategy: reference | digest | transform | evolve | playbook | procedure | checklist
pattern: required | optional | not_needed | TBD
playbook: <skill-name>
steps: []
trigger_examples: []
anti_trigger_examples: []
gate_policy_ids: []
eval_case_ids: []
updated_at: YYYY-MM-DD
needs_review: true | false   # optional
---
```

## Gate rules (minimal)

- `knowledge` must include `id`, `block_type`, `source_refs`, `summary`, `concepts`, `updated_at`, `version`, and `status`.
- `usage` must include `id`, `uses`, `intent`, `pattern`, `steps`, `updated_at`, and `playbook` for playbook strategies.
- `usage.uses` must reference existing `knowledge.name` entries.
- At gate level 2 or higher, `usage.uses` cannot contain `TBD`.
