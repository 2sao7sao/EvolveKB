from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

from evolvekb.evals.runner import eval_summary, run_evals


REPO = Path(__file__).resolve().parents[2]


def run_cmd(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([str(REPO), env["PYTHONPATH"]]) if env.get("PYTHONPATH") else str(REPO)
    return subprocess.run(args, cwd=REPO, env=env, text=True, capture_output=True, check=False)


def test_refund_eval_matrix_passes_core_categories() -> None:
    patterns = [
        "evals/retrieval_refund_policy.yaml",
        "evals/claim_extraction_refund_policy.yaml",
        "evals/grounding_answer_with_evidence.yaml",
        "evals/routing_refund_agent.yaml",
        "evals/playbook_refund_decision.yaml",
        "evals/evolution_safety_refund_policy.yaml",
        "evals/baseline_retrieval_vs_playbook.yaml",
    ]
    results = run_evals(REPO, patterns)

    assert len(results) == len(patterns)
    assert all(result.passed for result in results), [result.message for result in results]
    categories = {result.category for result in results}
    assert categories == {
        "retrieval_eval",
        "claim_extraction_eval",
        "grounding_eval",
        "routing_eval",
        "playbook_execution_eval",
        "evolution_safety_eval",
        "baseline_comparison_eval",
    }
    baseline = next(result for result in results if result.category == "baseline_comparison_eval")
    assert baseline.details["capability_delta"] >= 0.8


def test_eval_summary_json_includes_result_details() -> None:
    results = run_evals(REPO, ["evals/baseline_retrieval_vs_playbook.yaml"])
    summary = eval_summary(results)

    assert summary["total"] == 1
    assert summary["passed"] == 1
    assert summary["failed"] == 0
    assert summary["results"][0]["details"]["capability_delta"] >= 0.8


def test_cli_eval_run_writes_json_summary(tmp_path: Path) -> None:
    output_path = tmp_path / "eval-summary.json"
    result = run_cmd(
        sys.executable,
        "-m",
        "evolvekb.cli",
        "eval",
        "run",
        "evals/baseline_retrieval_vs_playbook.yaml",
        "--output",
        str(output_path),
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert "[eval-summary]" in result.stdout
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["total"] == 1
    assert payload["passed"] == 1
    assert payload["results"][0]["details"]["capability_delta"] >= 0.8


def test_cli_eval_run_can_print_json_summary() -> None:
    result = run_cmd(
        sys.executable,
        "-m",
        "evolvekb.cli",
        "eval",
        "run",
        "evals/baseline_retrieval_vs_playbook.yaml",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["total"] == 1
    assert payload["passed"] == 1
    assert payload["results"][0]["category"] == "baseline_comparison_eval"
