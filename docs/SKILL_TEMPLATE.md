# SKILL.md Template

Use this template when adding a new EvolveKB skill under `skills/<skill-name>/SKILL.md`.
Keep the skill deterministic, reviewable, and small enough for another contributor
to inspect.

```markdown
---
schema_version: 2
name: my-skill-name
description: One sentence describing the behavior this skill makes repeatable.
allowed-tools:
  - Read
metadata:
  kind: procedure
  intent: optional_runtime_intent_for_playbooks
  inputs:
    question: str
    evidence: list
  outputs:
    answer_md: str
  steps:
    - call: retrieve-evidence
    - call: compose-answer-md
  preconditions:
    - Source evidence is available or the caller accepts an empty evidence result.
  postconditions:
    - Output names every source used for a claim.
  supporting_files: []
  examples:
    - input:
        question: What does the policy require?
      output:
        answer_md: Evidence-backed answer...
  version: 0.3.0
---

# My Skill Name

## When To Use

Use this skill when the agent needs to produce a repeatable behavior from
reviewed knowledge assets.

## Procedure

1. State the intent and the relevant knowledge assets.
2. Retrieve or inspect evidence before writing claims.
3. Run the listed procedure steps in order.
4. Return output in the declared schema.
5. Call out missing evidence instead of inventing it.

## Failure Modes

- Required evidence is missing.
- The input intent does not match the skill.
- A downstream procedure returns an empty or invalid output.
```

## Field Notes

| Field | Requirement |
| --- | --- |
| `name` | Kebab-case directory name, matching `skills/<name>/`. |
| `description` | Non-empty behavior summary, not marketing copy. |
| `allowed-tools` | Keep narrow; do not grant write tools unless needed. |
| `metadata.kind` | Use `procedure` for callable steps and `playbook` for intent-routing entry points. |
| `metadata.intent` | Required for playbooks that `PlaybookRuntime` should route to. |
| `metadata.steps` | Use existing procedure names where possible. |
| `metadata.version` | Start new EvolveKB v0.3 skills at `0.3.0`. |

## Quality Checks

```bash
python -m evolvekb.cli validate --settings settings/evolve.yaml
python -m evolvekb.cli skills inspect my-skill-name
python -m pytest -q
```
