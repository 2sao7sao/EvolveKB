cat > settings/SCHEMA.md << 'MD'
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

## Example

```yaml
knowledge_mode: reference
gate_level: 1
auto_evolve: false
max_skill_md_bytes: 50000
