from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Sequence
import shutil
import tempfile

from evolvekb.evolution.proposal import list_proposals
from evolvekb.gates.engine import validate_repo
from evolvekb.ingestion.compiler import compile_markdown
from evolvekb.retrieval.keyword import keyword_retrieve


DEFAULT_DEMO_DOC = "examples/refund_policy.md"
DEFAULT_DEMO_SETTINGS = "settings/evolve.yaml"
DEFAULT_DEMO_EVALS = [
    "evals/retrieval_execution_first.yaml",
    "evals/routing_answer_with_evidence.yaml",
]


@dataclass(frozen=True)
class ProductMetric:
    key: str
    value: float
    numerator: int
    denominator: int
    explanation: str


@dataclass(frozen=True)
class FlagshipDemoReport:
    workspace: str
    doc: str
    source_id: str
    claim_count: int
    grounded_claim_count: int
    concept_count: int
    proposal_path: str | None
    gate_total: int
    gate_failed: int
    eval_total: int
    eval_passed: int
    proposal_count: int
    retrieval_baseline_steps: dict[str, bool]
    playbook_runtime_steps: dict[str, bool]
    metrics: dict[str, ProductMetric]

    @property
    def passed(self) -> bool:
        return self.gate_failed == 0 and self.eval_passed == self.eval_total


def run_flagship_demo(
    repo: Path,
    doc: str = DEFAULT_DEMO_DOC,
    settings: str = DEFAULT_DEMO_SETTINGS,
    eval_patterns: Sequence[str] | None = None,
) -> FlagshipDemoReport:
    """Run the product demo in an isolated copy so the source repo stays clean."""

    with tempfile.TemporaryDirectory(prefix="evolvekb-demo-") as temp_dir:
        workspace = Path(temp_dir) / "EvolveKB"
        _copy_repo(repo, workspace)
        report = run_flagship_demo_in_workspace(
            workspace,
            doc=doc,
            settings=settings,
            eval_patterns=eval_patterns,
        )
        return replace(report, workspace=f"{report.workspace} (removed after run)")


def run_flagship_demo_in_workspace(
    workspace: Path,
    doc: str = DEFAULT_DEMO_DOC,
    settings: str = DEFAULT_DEMO_SETTINGS,
    eval_patterns: Sequence[str] | None = None,
) -> FlagshipDemoReport:
    from evolvekb.evals.runner import run_evals

    patterns = list(eval_patterns or DEFAULT_DEMO_EVALS)
    ingest = compile_markdown(workspace, doc, write=True, proposal=True)
    gate_results = validate_repo(workspace, settings)
    failed_gates = [result for result in gate_results if not result.passed]
    eval_results = run_evals(workspace, patterns)
    proposal_rows = list_proposals(workspace)
    retrieval_items = keyword_retrieve(
        workspace,
        "refund manager approval finance evidence",
        limit=5,
    )

    grounded_claim_count = sum(1 for claim in ingest.claims if claim.evidence_quote.strip())
    retrieval_baseline_steps = {
        "retrieve_policy_text": bool(retrieval_items),
        "extract_grounded_claims": False,
        "run_validation_gates": False,
        "run_regression_evals": False,
        "create_reviewable_proposal": False,
    }
    playbook_runtime_steps = {
        "retrieve_policy_text": bool(retrieval_items),
        "extract_grounded_claims": grounded_claim_count == len(ingest.claims) and bool(ingest.claims),
        "run_validation_gates": not failed_gates,
        "run_regression_evals": bool(eval_results)
        and all(result.passed for result in eval_results),
        "create_reviewable_proposal": ingest.proposal_path is not None,
    }
    metrics = _build_metrics(
        claim_count=len(ingest.claims),
        grounded_claim_count=grounded_claim_count,
        gate_failed=len(failed_gates),
        eval_total=len(eval_results),
        eval_passed=sum(1 for result in eval_results if result.passed),
        proposal_created=ingest.proposal_path is not None,
        proposal_count=len(proposal_rows),
        retrieval_baseline_steps=retrieval_baseline_steps,
        playbook_runtime_steps=playbook_runtime_steps,
    )

    return FlagshipDemoReport(
        workspace=str(workspace),
        doc=doc,
        source_id=ingest.source.id,
        claim_count=len(ingest.claims),
        grounded_claim_count=grounded_claim_count,
        concept_count=len(ingest.concepts),
        proposal_path=str(ingest.proposal_path.relative_to(workspace))
        if ingest.proposal_path
        else None,
        gate_total=len(gate_results),
        gate_failed=len(failed_gates),
        eval_total=len(eval_results),
        eval_passed=sum(1 for result in eval_results if result.passed),
        proposal_count=len(proposal_rows),
        retrieval_baseline_steps=retrieval_baseline_steps,
        playbook_runtime_steps=playbook_runtime_steps,
        metrics=metrics,
    )


def format_demo_report(report: FlagshipDemoReport) -> str:
    status = "PASS" if report.passed else "FAIL"
    lines = [
        "# EvolveKB Flagship Demo",
        "",
        f"status: {status}",
        f"workspace: {report.workspace}",
        f"source_doc: {report.doc}",
        "",
        "## 1. Ingest policy into knowledge assets",
        f"- source_id: {report.source_id}",
        f"- claims: {report.claim_count}",
        f"- grounded_claims: {report.grounded_claim_count}",
        f"- concepts: {report.concept_count}",
        f"- proposal: {report.proposal_path or 'not generated'}",
        "",
        "## 2. Run gates and regression evals",
        f"- gates: {_format_gate_status(report)}",
        f"- evals: {report.eval_passed}/{report.eval_total} passed",
        f"- pending_proposals: {report.proposal_count}",
        "",
        "## 3. Product metrics",
    ]
    for metric in report.metrics.values():
        lines.append(
            f"- {metric.key}: {metric.value:.2f} "
            f"({metric.numerator}/{metric.denominator}) - {metric.explanation}"
        )

    lines.extend(
        [
            "",
            "## 4. Retrieval-only baseline coverage",
            _format_steps(report.retrieval_baseline_steps),
            "",
            "## 5. Execution-first playbook coverage",
            _format_steps(report.playbook_runtime_steps),
        ]
    )
    return "\n".join(lines) + "\n"


def _build_metrics(
    *,
    claim_count: int,
    grounded_claim_count: int,
    gate_failed: int,
    eval_total: int,
    eval_passed: int,
    proposal_created: bool,
    proposal_count: int,
    retrieval_baseline_steps: dict[str, bool],
    playbook_runtime_steps: dict[str, bool],
) -> dict[str, ProductMetric]:
    retrieval_score = _coverage(retrieval_baseline_steps)
    playbook_score = _coverage(playbook_runtime_steps)
    proposal_gate_pass = int(proposal_created and proposal_count > 0 and gate_failed == 0)

    return {
        "claim_grounding_rate": ProductMetric(
            key="claim_grounding_rate",
            value=_ratio(grounded_claim_count, claim_count),
            numerator=grounded_claim_count,
            denominator=claim_count,
            explanation="extracted claims that keep a source evidence quote",
        ),
        "playbook_success_rate": ProductMetric(
            key="playbook_success_rate",
            value=_ratio(eval_passed, eval_total),
            numerator=eval_passed,
            denominator=eval_total,
            explanation="seed routing/retrieval evals passed by the runtime",
        ),
        "proposal_gate_pass_rate": ProductMetric(
            key="proposal_gate_pass_rate",
            value=float(proposal_gate_pass),
            numerator=proposal_gate_pass,
            denominator=1,
            explanation="demo proposal created while repository gates remain green",
        ),
        "retrieval_vs_playbook_delta": ProductMetric(
            key="retrieval_vs_playbook_delta",
            value=playbook_score - retrieval_score,
            numerator=sum(playbook_runtime_steps.values()) - sum(retrieval_baseline_steps.values()),
            denominator=max(1, len(playbook_runtime_steps)),
            explanation="capability coverage gained over a retrieval-only baseline",
        ),
    }


def _copy_repo(source: Path, target: Path) -> None:
    shutil.copytree(
        source,
        target,
        ignore=shutil.ignore_patterns(
            ".git",
            ".mypy_cache",
            ".pytest_cache",
            ".ruff_cache",
            "__pycache__",
            "*.egg-info",
            ".venv",
            "build",
            "dist",
            "node_modules",
            "venv",
        ),
    )


def _coverage(steps: dict[str, bool]) -> float:
    return _ratio(sum(steps.values()), len(steps))


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def _format_steps(steps: dict[str, bool]) -> str:
    return "\n".join(f"- {name}: {'yes' if enabled else 'no'}" for name, enabled in steps.items())


def _format_gate_status(report: FlagshipDemoReport) -> str:
    if report.gate_failed:
        return f"FAIL ({report.gate_failed}/{report.gate_total} failed)"
    if report.gate_total:
        return f"PASS ({report.gate_total}/{report.gate_total} checks passed)"
    return "PASS (0 blocking failures)"
