from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

from evolvekb.skills.runtime import PlaybookRuntime


REPO = Path(__file__).resolve().parents[2]


def run_cmd(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([str(REPO), env["PYTHONPATH"]]) if env.get("PYTHONPATH") else str(REPO)
    return subprocess.run(args, cwd=REPO, env=env, text=True, capture_output=True, check=False)


def test_playbook_runtime_returns_step_trace() -> None:
    result = PlaybookRuntime(REPO).run(
        intent="answer_with_evidence",
        question="What is execution-first knowledge?",
        settings_arg="settings/reference.yaml",
        write_side_effects=False,
    )

    trace = result.trace
    assert trace.id.startswith("trace_")
    assert trace.intent == "answer_with_evidence"
    assert trace.mode == "reference"
    assert trace.selected_skill == "answer-with-evidence"
    assert trace.output_hash.startswith("sha256:")
    assert [step.procedure for step in trace.step_traces] == [
        "retrieve-evidence",
        "compose-evidence-answer",
    ]
    assert all(step.success for step in trace.step_traces)
    assert all(step.input_hash.startswith("sha256:") for step in trace.step_traces)
    assert all(step.output_hash.startswith("sha256:") for step in trace.step_traces)
    assert "execution-first-kb" in trace.retrieved_knowledge_ids
    assert trace.retrieval_plan["observed_modes"] == ["keyword"]
    assert trace.retrieval_plan["retrieval_traces"][0]["retriever"] == "keyword"
    gate_results = [gate for step in trace.step_traces for gate in step.gate_results]
    assert any(
        gate["gate_id"] == "skill_runtime_declared" and gate["severity"] == "info"
        for gate in gate_results
    )
    assert any(
        gate["gate_id"] == "skill_runtime_declared" and gate["severity"] == "warning"
        for gate in gate_results
    )


def test_cli_run_writes_trace_json(tmp_path: Path) -> None:
    trace_path = tmp_path / "trace.json"
    result = run_cmd(
        sys.executable,
        "-m",
        "evolvekb.cli",
        "run",
        "--intent",
        "answer_with_evidence",
        "--question",
        "What is execution-first knowledge?",
        "--settings",
        "settings/reference.yaml",
        "--no-side-effects",
        "--trace-out",
        str(trace_path),
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert trace_path.exists()
    payload = json.loads(trace_path.read_text(encoding="utf-8"))
    assert payload["intent"] == "answer_with_evidence"
    assert payload["selected_skill"] == "answer-with-evidence"
    assert payload["step_traces"][0]["procedure"] == "retrieve-evidence"
    assert payload["step_traces"][0]["success"] is True
    assert payload["retrieved_knowledge_ids"] == ["execution-first-kb"]
    assert "[trace]" in result.stdout
