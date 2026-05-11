from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from evolvekb.retrieval.keyword import keyword_retrieve
from evolvekb.skills.registry import SkillRegistry


@dataclass
class EvalResult:
    id: str
    category: str
    passed: bool
    message: str


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
    return EvalResult(eval_id, category, False, f"unsupported eval category: {category}")


def run_evals(repo: Path, patterns: list[str]) -> list[EvalResult]:
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(sorted(repo.glob(pattern)))
    return [run_eval_file(repo, path) for path in paths]


def _run_retrieval_eval(repo: Path, eval_id: str, data: dict[str, Any]) -> EvalResult:
    query = str((data.get("input") or {}).get("query") or "")
    expected = data.get("expected") or {}
    required = set(expected.get("must_retrieve") or [])
    items = keyword_retrieve(repo, query, limit=int(expected.get("limit") or 5))
    names = {item.name for item in items}
    missing = required - names
    if missing:
        return EvalResult(eval_id, "retrieval_eval", False, f"missing retrieval targets: {sorted(missing)}")
    return EvalResult(eval_id, "retrieval_eval", True, f"retrieved {len(items)} item(s)")


def _run_routing_eval(repo: Path, eval_id: str, data: dict[str, Any]) -> EvalResult:
    expected = data.get("expected") or {}
    intent = str((data.get("input") or {}).get("intent") or "")
    wanted = expected.get("selected_playbook")
    try:
        skill = SkillRegistry.load(repo).pick_playbook(intent)
    except KeyError as exc:
        return EvalResult(eval_id, "routing_eval", False, str(exc))
    if wanted and skill.name != wanted:
        return EvalResult(eval_id, "routing_eval", False, f"expected {wanted}, got {skill.name}")
    return EvalResult(eval_id, "routing_eval", True, f"selected {skill.name}")


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
        return EvalResult(eval_id, "capability_coverage_eval", False, "; ".join(failures))
    return EvalResult(
        eval_id,
        "capability_coverage_eval",
        True,
        f"metrics passed: {', '.join(sorted(report.metrics))}",
    )
