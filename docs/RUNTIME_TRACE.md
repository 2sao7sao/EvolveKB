# Runtime Trace

EvolveKB records a `RunTrace` for every playbook run. The current v0.4 track
supports Python `runtime.entrypoint` procedures and keeps the legacy `PROC_IMPL`
map as a compatibility fallback.

## What Gets Traced

| Field | Meaning |
| --- | --- |
| `id` | Trace id for the playbook run. |
| `intent` | Runtime intent selected by the caller. |
| `mode` | Loaded knowledge mode from settings. |
| `selected_skill` | Playbook selected by the skill registry. |
| `retrieval_plan.settings` | Retrieval settings used by the run. |
| `retrieval_plan.observed_modes` | Retrieval modes observed in evidence packs. |
| `retrieval_plan.retrieval_traces` | Mode-specific retrieval trace payloads. |
| `retrieved_knowledge_ids` | Knowledge assets observed in evidence packs. |
| `step_traces` | One trace per procedure call. |
| `output_hash` | Stable hash of the rendered output. |

Each `StepTrace` includes:

```text
step_index, procedure, input_hash, output_hash, started_at, finished_at,
duration_ms, success, error, retrieved_knowledge_ids, evidence_ids, gate_results
```

`gate_results` is the list of gate policy results that fired during this step
(e.g. `skill_runtime_declared` warnings when a procedure relies on the legacy
`PROC_IMPL` fallback instead of `metadata.runtime.entrypoint`). Empty for
entrypoint-backed steps.

## CLI

Print trace JSON before the rendered output:

```bash
python -m evolvekb.cli run \
  --intent answer_with_evidence \
  --question "What is execution-first knowledge?" \
  --settings settings/reference.yaml \
  --no-side-effects \
  --trace
```

Write the trace to a file:

```bash
python -m evolvekb.cli run \
  --intent answer_with_evidence \
  --question "What is execution-first knowledge?" \
  --settings settings/reference.yaml \
  --no-side-effects \
  --trace-out outputs/traces/latest.json
```

## Harness Usage

```python
from pathlib import Path

from evolvekb.skills.runtime import PlaybookRuntime

runtime = PlaybookRuntime(Path("."))
result = runtime.run(
    intent="answer_with_evidence",
    question="What does the KB say about execution-first knowledge?",
    settings_arg="settings/reference.yaml",
    write_side_effects=False,
)

print(result.rendered)
print(result.trace.id)
```

## Python Procedure Entrypoints

Procedure skills can declare a Python entrypoint:

```yaml
metadata:
  kind: procedure
  runtime:
    type: python
    entrypoint: evolvekb.procedures.retrieve_evidence:run
    timeout_ms: 3000
    side_effects: false
```

The entrypoint must be a callable with this shape:

```python
from pathlib import Path
from typing import Any

from evolvekb.core.models import SkillAsset


def run(
    *,
    repo: Path,
    skill: SkillAsset,
    env: dict[str, Any],
    args: dict[str, Any],
) -> Any:
    ...
```

If a procedure has no `runtime.entrypoint`, EvolveKB uses the legacy `PROC_IMPL`
fallback during v0.3.x.

Entrypoint-backed procedures may declare `runtime.side_effects: true`. Those
procedures are blocked when the runtime is called with `write_side_effects=False`
or the CLI uses `--no-side-effects`, so eval and CI paths can stay read-only.

## Boundaries

- Trace timestamps and durations are runtime observations, not deterministic
  benchmark data.
- Input, output, and final output hashes are deterministic for deterministic
  fixtures.
- Procedure execution supports Python `runtime.entrypoint` declarations. Skills
  without an entrypoint still use the legacy `PROC_IMPL` fallback during v0.3.x.
- Legacy fallback usage is recorded as a `skill_runtime_declared` warning in
  each affected step trace.
