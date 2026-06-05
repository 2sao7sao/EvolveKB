# Runtime Trace

EvolveKB records a `RunTrace` for every playbook run. The current v0.4 track
trace wraps the legacy `PROC_IMPL` procedure path; it does not yet replace the
procedure executor with dynamic entrypoints.

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
duration_ms, success, error, retrieved_knowledge_ids, evidence_ids
```

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

## Boundaries

- Trace timestamps and durations are runtime observations, not deterministic
  benchmark data.
- Input, output, and final output hashes are deterministic for deterministic
  fixtures.
- Procedure execution still uses the legacy `PROC_IMPL` map in this milestone.
  Dynamic runtime entrypoints belong to the next executor milestone.
