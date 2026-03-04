# Knowledge Base Schema

This folder separates knowledge assets and usage assets.

## knowledge/

Stores distilled, model‑understood knowledge.

Required frontmatter:

```yaml
---
name: <kebab-name>
kind: knowledge
source: <path or url>
summary: <one paragraph>
concepts: [list, of, concepts]
updated_at: YYYY-MM-DD
---
```

## usage/

Stores how to use knowledge (playbooks / procedures / strategies).

Required frontmatter:

```yaml
---
name: <kebab-name>
kind: usage
uses: [knowledge-name-1, knowledge-name-2]
strategy: playbook | procedure | checklist
steps: []
---
```

## Gate rules (minimal)

- `knowledge` must include `source`, `summary`, `concepts`, `updated_at`.
- `usage` must include `uses` and `steps`.
- `usage.uses` must reference existing `knowledge.name` entries.
