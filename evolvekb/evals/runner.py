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
