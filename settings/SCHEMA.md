# Settings Schema

This document defines the supported keys in a settings YAML file (e.g. `settings/default.yaml`).

## Top-level keys

### `knowledge_mode` (string)

How the knowledge should be used in the agent runtime.

Allowed values:
- `reference` — retrieve/quote when needed, avoid rewriting the KB
- `digest` — produce structured summaries first, then answer
- `transform` — compile knowledge into reusable procedures/playbooks
- `evolve` — propose KB updates under gates (versioned, reviewable)

Default: `reference`

### `output_template` (string)

How verbose the rendered output should be.

Allowed values:
- `compact` — only the core answer
- `expanded` — include digest/transform/evolve blocks

Default: `expanded`

### `gate_level` (int)

How strict the validation/evolution gates should be.

Allowed values: `0..3`

- `0`: permissive (experiments)
- `1`: basic checks (format, presence)
- `2`: stricter checks (limits, structure)
- `3`: strict (write-back requires reviewable evidence)

Default: `1`

### `auto_evolve` (bool)

Whether the system is allowed to automatically propose KB updates (PR-like patches).

Default: `false`

### `max_skill_md_bytes` (int)

Soft/hard limit used by validators to keep skills lean.

Default: `50000`

### `retrieval` (mapping)

Optional retrieval feature flags and default retriever selection.

Supported keys:
- `default_mode` — `keyword`, `bm25`, `hybrid`, or `semantic`
- `modes.keyword.enabled`
- `modes.bm25.enabled`
- `modes.semantic.enabled`
- `modes.hybrid.enabled`
- `modes.hybrid.weights.keyword`
- `modes.hybrid.weights.bm25`
- `modes.hybrid.weights.semantic`
- `modes.hybrid.weights.evidence`

Default quickstart behavior uses `keyword` so no external API key or vector
store is required. `semantic` is a deterministic local semantic-lite retriever,
not an embedding API integration.

### `proposal` (mapping)

Proposal workflow controls.

Supported keys:
- `require_human_review`

### `gates` (mapping)

Gate thresholds and policy switches.

Supported keys:
- `citation_coverage_min`
- `allow_tbd_usage`

## Example

```yaml
knowledge_mode: reference
output_template: compact
gate_level: 1
auto_evolve: false
max_skill_md_bytes: 50000
retrieval:
  default_mode: keyword
  modes:
    keyword:
      enabled: true
    bm25:
      enabled: true
    semantic:
      enabled: true
    hybrid:
      enabled: true
      weights:
        keyword: 0.35
        bm25: 0.35
        semantic: 0.2
        evidence: 0.1
proposal:
  require_human_review: true
gates:
  citation_coverage_min: 0.8
  allow_tbd_usage: false
```
