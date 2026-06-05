from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from pathlib import Path
import shutil
import tempfile
from typing import Any

import yaml

from evolvekb.gates.engine import validate_repo
from evolvekb.ingestion.compiler import compile_markdown
from evolvekb.retrieval.registry import get_retriever
from evolvekb.skills.registry import SkillRegistry
from evolvekb.skills.runtime import PlaybookRuntime


@dataclass
class EvalResult:
    id: str
    category: str
    passed: bool
    message: str
    details: dict[str, Any] = field(default_factory=dict)


def run_eval_file(repo: Path, path: Path) -> EvalResult:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    category = str(data.get("category") or "unknown")
    eval_id = str(data.get("id") or path.stem)
    if category == "retrieval_eval":
        return _run_retrieval_eval(repo, eval_id, data)
    if category == "routing_eval":
        return _run_routing_eval(repo, eval_id, data)
    if category == "capability_coverage_eval":
        return _run_capability_coverage_eval(repo, eval_id, data)
    if category == "claim_extraction_eval":
        return _run_claim_extraction_eval(repo, eval_id, data)
    if category == "grounding_eval":
        return _run_grounding_eval(repo, eval_id, data)
    if category == "playbook_execution_eval":
        return _run_playbook_execution_eval(repo, eval_id, data)
    if category == "baseline_comparison_eval":
        return _run_baseline_comparison_eval(repo, eval_id, data)
    if category == "evolution_safety_eval":
        return _run_evolution_safety_eval(repo, eval_id, data)
    return EvalResult(eval_id, category, False, f"unsupported eval category: {category}")


def run_evals(repo: Path, patterns: list[str]) -> list[EvalResult]:
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(sorted(repo.glob(pattern)))
    return [run_eval_file(repo, path) for path in paths]


def eval_summary(results: list[EvalResult]) -> dict[str, Any]:
    passed = sum(1 for result in results if result.passed)
    return {
        "total": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "results": [asdict(result) for result in results],
    }


def _run_retrieval_eval(repo: Path, eval_id: str, data: dict[str, Any]) -> EvalResult:
    input_data = data.get("input") or {}
    query = str(input_data.get("query") or "")
    retriever_name = str(input_data.get("retriever") or "keyword")
    expected = data.get("expected") or {}
    required = set(expected.get("must_retrieve") or [])
    with _prepared_workspace(repo, input_data) as workspace:
        try:
            pack = get_retriever(retriever_name).retrieve(
                workspace,
                query,
                limit=int(expected.get("limit") or 5),
            )
        except Exception as exc:
            return EvalResult(eval_id, "retrieval_eval", False, f"{retriever_name} failed: {exc}")
    names = {item.name for item in pack.items}
    missing = required - names
    if missing:
        return EvalResult(
            eval_id,
            "retrieval_eval",
            False,
            f"{retriever_name} missing retrieval targets: {sorted(missing)}",
            {"retrieved": sorted(names), "required": sorted(required)},
        )
    return EvalResult(
        eval_id,
        "retrieval_eval",
        True,
        f"{retriever_name} retrieved {len(pack.items)} item(s)",
        {"retrieved": sorted(names), "retriever": retriever_name},
    )


def _run_routing_eval(repo: Path, eval_id: str, data: dict[str, Any]) -> EvalResult:
    expected = data.get("expected") or {}
    intent = str((data.get("input") or {}).get("intent") or "")
    wanted = expected.get("selected_playbook")
    try:
        skill = SkillRegistry.load(repo).pick_playbook(intent)
    except KeyError as exc:
        return EvalResult(eval_id, "routing_eval", False, str(exc), {"intent": intent})
    if wanted and skill.name != wanted:
        return EvalResult(
            eval_id,
            "routing_eval",
            False,
            f"expected {wanted}, got {skill.name}",
            {"intent": intent, "selected_playbook": skill.name},
        )
    return EvalResult(
        eval_id,
        "routing_eval",
        True,
        f"selected {skill.name}",
        {"intent": intent, "selected_playbook": skill.name},
    )


def _run_capability_coverage_eval(repo: Path, eval_id: str, data: dict[str, Any]) -> EvalResult:
    from evolvekb.demo import DEFAULT_DEMO_EVALS, DEFAULT_DEMO_SETTINGS, run_flagship_demo

    input_data = data.get("input") or {}
    expected = data.get("expected") or {}
    report = run_flagship_demo(
        repo,
        doc=str(input_data.get("doc") or "examples/refund_policy.md"),
        settings=str(input_data.get("settings") or DEFAULT_DEMO_SETTINGS),
        eval_patterns=input_data.get("eval_patterns") or DEFAULT_DEMO_EVALS,
    )
    failures: list[str] = []
    for metric_name, min_value in (expected.get("min_metrics") or {}).items():
        metric = report.metrics.get(str(metric_name))
        if metric is None:
            failures.append(f"missing metric {metric_name}")
            continue
        if metric.value < float(min_value):
            failures.append(f"{metric_name}={metric.value:.2f} < {float(min_value):.2f}")
    if expected.get("must_create_proposal") and not report.proposal_path:
        failures.append("proposal was not created")
    if expected.get("must_pass_gates") and report.gate_failed:
        failures.append(f"{report.gate_failed} gate(s) failed")
    if failures:
        return EvalResult(
            eval_id,
            "capability_coverage_eval",
            False,
            "; ".join(failures),
            {"failures": failures},
        )
    return EvalResult(
        eval_id,
        "capability_coverage_eval",
        True,
        f"metrics passed: {', '.join(sorted(report.metrics))}",
        {
            "metrics": {
                name: {
                    "value": metric.value,
                    "numerator": metric.numerator,
                    "denominator": metric.denominator,
                }
                for name, metric in report.metrics.items()
            }
        },
    )


def _run_claim_extraction_eval(repo: Path, eval_id: str, data: dict[str, Any]) -> EvalResult:
    input_data = data.get("input") or {}
    expected = data.get("expected") or {}
    result = compile_markdown(repo, str(input_data.get("doc") or ""), write=False, proposal=False)
    failures: list[str] = []
    min_claims = int(expected.get("min_claims") or 1)
    if len(result.claims) < min_claims:
        failures.append(f"claim_count={len(result.claims)} < {min_claims}")
    if expected.get("require_evidence") and any(not claim.evidence_quote for claim in result.claims):
        failures.append("one or more claims missing evidence_quote")
    if failures:
        return EvalResult(
            eval_id,
            "claim_extraction_eval",
            False,
            "; ".join(failures),
            {"claim_count": len(result.claims), "failures": failures},
        )
    return EvalResult(
        eval_id,
        "claim_extraction_eval",
        True,
        f"extracted {len(result.claims)} claim(s)",
        {"claim_count": len(result.claims), "source_id": result.source.id},
    )


def _run_grounding_eval(repo: Path, eval_id: str, data: dict[str, Any]) -> EvalResult:
    input_data = data.get("input") or {}
    expected = data.get("expected") or {}
    with _prepared_workspace(repo, input_data) as workspace:
        result = PlaybookRuntime(workspace).run(
            intent=str(input_data.get("intent") or "answer_with_evidence"),
            question=str(input_data.get("question") or ""),
            settings_arg=input_data.get("settings") or "settings/reference.yaml",
            write_side_effects=False,
        )
    failures = _contains_failures(result.rendered, expected.get("must_contain") or [])
    min_evidence_ids = int(expected.get("min_evidence_ids") or 1)
    evidence_ids = sorted({evidence_id for trace in result.trace.step_traces for evidence_id in trace.evidence_ids})
    if len(evidence_ids) < min_evidence_ids:
        failures.append(f"evidence_id_count={len(evidence_ids)} < {min_evidence_ids}")
    if failures:
        return EvalResult(
            eval_id,
            "grounding_eval",
            False,
            "; ".join(failures),
            {"trace_id": result.trace.id, "evidence_ids": evidence_ids, "failures": failures},
        )
    return EvalResult(
        eval_id,
        "grounding_eval",
        True,
        f"grounded answer used {len(evidence_ids)} evidence id(s)",
        {"trace_id": result.trace.id, "evidence_ids": evidence_ids},
    )


def _run_playbook_execution_eval(repo: Path, eval_id: str, data: dict[str, Any]) -> EvalResult:
    input_data = data.get("input") or {}
    expected = data.get("expected") or {}
    with _prepared_workspace(repo, input_data) as workspace:
        result = PlaybookRuntime(workspace).run(
            intent=str(input_data.get("intent") or ""),
            question=str(input_data.get("question") or ""),
            settings_arg=input_data.get("settings") or "settings/reference.yaml",
            write_side_effects=False,
        )
    step_names = [step.procedure for step in result.trace.step_traces]
    failures = _contains_failures(result.rendered, expected.get("must_contain") or [])
    selected = expected.get("selected_playbook")
    if selected and result.trace.selected_skill != selected:
        failures.append(f"expected playbook {selected}, got {result.trace.selected_skill}")
    required_steps = list(expected.get("required_steps") or [])
    missing_steps = [step for step in required_steps if step not in step_names]
    if missing_steps:
        failures.append(f"missing steps: {missing_steps}")
    if failures:
        return EvalResult(
            eval_id,
            "playbook_execution_eval",
            False,
            "; ".join(failures),
            {"trace_id": result.trace.id, "steps": step_names, "failures": failures},
        )
    return EvalResult(
        eval_id,
        "playbook_execution_eval",
        True,
        f"executed {result.trace.selected_skill} with {len(step_names)} step(s)",
        {"trace_id": result.trace.id, "steps": step_names},
    )


def _run_baseline_comparison_eval(repo: Path, eval_id: str, data: dict[str, Any]) -> EvalResult:
    fixture = data.get("fixture") or {}
    input_data = {
        "source_docs": fixture.get("source_docs") or (data.get("input") or {}).get("source_docs") or []
    }
    expected = data.get("expected") or {}
    baseline = data.get("baseline") or {}
    runtime_config = data.get("runtime") or {}
    query = str(data.get("query") or (data.get("input") or {}).get("query") or "")
    required_capabilities = list(expected.get("required_capabilities") or [])
    with _prepared_workspace(repo, input_data) as workspace:
        retrieval_pack = get_retriever("keyword").retrieve(workspace, query, limit=5)
        playbook = runtime_config.get("playbook") or {}
        result = PlaybookRuntime(workspace).run(
            intent=str(playbook.get("intent") or "refund_decision"),
            question=query,
            settings_arg=playbook.get("settings") or "settings/reference.yaml",
            write_side_effects=False,
        )
    baseline_allowed = set((baseline.get("retrieval_only") or {}).get("allowed_capabilities") or [])
    baseline_capabilities = {
        capability: capability in baseline_allowed and capability == "find_relevant_text" and bool(retrieval_pack.items)
        for capability in required_capabilities
    }
    playbook_capabilities = _playbook_capability_map(required_capabilities, result)
    baseline_count = sum(baseline_capabilities.values())
    playbook_count = sum(playbook_capabilities.values())
    denominator = max(1, len(required_capabilities))
    delta = (playbook_count - baseline_count) / denominator
    min_delta = float(expected.get("min_delta") if expected.get("min_delta") is not None else 0.0)
    if delta < min_delta:
        return EvalResult(
            eval_id,
            "baseline_comparison_eval",
            False,
            f"capability_delta={delta:.2f} < {min_delta:.2f}",
            {
                "baseline": baseline_capabilities,
                "playbook": playbook_capabilities,
                "capability_delta": delta,
            },
        )
    return EvalResult(
        eval_id,
        "baseline_comparison_eval",
        True,
        f"capability_delta={delta:.2f} ({playbook_count - baseline_count}/{denominator})",
        {
            "baseline": baseline_capabilities,
            "playbook": playbook_capabilities,
            "capability_delta": delta,
            "numerator": playbook_count - baseline_count,
            "denominator": denominator,
        },
    )


def _run_evolution_safety_eval(repo: Path, eval_id: str, data: dict[str, Any]) -> EvalResult:
    input_data = data.get("input") or {}
    expected = data.get("expected") or {}
    with tempfile.TemporaryDirectory(prefix="evolvekb-eval-") as temp_dir:
        workspace = Path(temp_dir) / "EvolveKB"
        _copy_repo(repo, workspace)
        result = compile_markdown(
            workspace,
            str(input_data.get("doc") or ""),
            write=True,
            proposal=True,
        )
        failed_gates = [item for item in validate_repo(workspace, input_data.get("settings") or "settings/evolve.yaml") if not item.passed]
    failures: list[str] = []
    if expected.get("must_create_proposal") and not result.proposal_path:
        failures.append("proposal was not created")
    if expected.get("must_pass_gates") and failed_gates:
        failures.append(f"{len(failed_gates)} gate(s) failed")
    if failures:
        return EvalResult(
            eval_id,
            "evolution_safety_eval",
            False,
            "; ".join(failures),
            {"failures": failures, "gate_failures": [gate.message for gate in failed_gates]},
        )
    return EvalResult(
        eval_id,
        "evolution_safety_eval",
        True,
        "proposal created and gates passed",
        {
            "proposal_path": str(result.proposal_path.relative_to(workspace)) if result.proposal_path else None,
            "gate_failures": 0,
        },
    )


def _contains_failures(text: str, must_contain: list[Any]) -> list[str]:
    return [f"missing output text: {needle}" for needle in must_contain if str(needle) not in text]


def _playbook_capability_map(required_capabilities: list[str], result: Any) -> dict[str, bool]:
    text = str(result.rendered)
    steps_passed = bool(result.trace.step_traces) and all(step.success for step in result.trace.step_traces)
    evidence_ids = sorted({evidence_id for step in result.trace.step_traces for evidence_id in step.evidence_ids})
    return {
        capability: {
            "find_relevant_text": bool(result.trace.retrieved_knowledge_ids),
            "cite_grounded_claim": bool(evidence_ids) and "Evidence IDs" in text,
            "route_to_refund_playbook": result.trace.selected_skill == "refund-decision",
            "execute_policy_steps": steps_passed,
            "produce_reviewable_decision": "Decision:" in text and "Source Refs" in text,
        }.get(capability, False)
        for capability in required_capabilities
    }


@contextmanager
def _prepared_workspace(repo: Path, input_data: dict[str, Any]):
    source_docs = list(input_data.get("source_docs") or [])
    if not source_docs:
        yield repo
        return
    with tempfile.TemporaryDirectory(prefix="evolvekb-eval-") as temp_dir:
        workspace = Path(temp_dir) / "EvolveKB"
        _copy_repo(repo, workspace)
        for doc in source_docs:
            compile_markdown(workspace, str(doc), write=True, proposal=False)
        yield workspace


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
