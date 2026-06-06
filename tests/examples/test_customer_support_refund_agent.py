from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[2]


def run_cmd(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([str(REPO), env["PYTHONPATH"]]) if env.get("PYTHONPATH") else str(REPO)
    return subprocess.run(args, cwd=REPO, env=env, text=True, capture_output=True, check=False)


def test_customer_support_refund_agent_demo_outputs_evidence_trace_and_proposal() -> None:
    result = run_cmd(sys.executable, "examples/customer_support_refund_agent.py")

    assert result.returncode == 0, result.stderr or result.stdout
    assert "# Customer Support Refund Agent Demo" in result.stdout
    assert "knowledge_path: kb/knowledge/customer-support-refund-policy.md" in result.stdout
    assert "proposal_path: kb/proposals/" in result.stdout
    assert "playbook: refund-decision" in result.stdout
    assert "trace_id: trace_" in result.stdout
    assert "retrieved_knowledge_ids: customer-support-refund-policy" in result.stdout
    assert "Decision: needs_review" in result.stdout
    assert "Evidence IDs" in result.stdout
    assert "Source Refs" in result.stdout
    assert "gates: PASS" in result.stdout
