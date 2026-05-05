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

Optional retrieval feature flags. Phase 2 Milestone 1+2 only stores these settings; retrieval implementations arrive in later milestones.

Supported keys:
- `keyword`
- `vector`
- `graph`

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
  keyword: true
  vector: false
  graph: false
proposal:
  require_human_review: true
gates:
  citation_coverage_min: 0.8
  allow_tbd_usage: false
```
