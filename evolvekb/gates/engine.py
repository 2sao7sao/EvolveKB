from __future__ import annotations

import os
from pathlib import Path

from evolvekb.assets.registry import AssetRegistry
from evolvekb.core.config import load_settings
from evolvekb.core.models import GateResult


def validate_repo(repo: Path, settings_arg: str | Path | None = None) -> list[GateResult]:
    settings = load_settings(repo, settings_arg)
    registry = AssetRegistry.load(repo)
    results = registry.validation_results(settings.gate_level)
    results.extend(validate_leanness(repo, settings.max_skill_md_bytes))
    return results


def validate_leanness(repo: Path, max_skill_md_bytes: int) -> list[GateResult]:
    results: list[GateResult] = []
    skills_root = repo / "skills"
    if not skills_root.exists():
        return results

    max_total_skills = int(os.environ.get("MAX_SKILLS", "500"))
    skill_dirs = [p for p in skills_root.iterdir() if p.is_dir() and (p / "SKILL.md").exists()]
    if len(skill_dirs) > max_total_skills:
        results.append(
            GateResult(
                gate_id="skill_leanness",
                passed=False,
                severity="error",
                message=f"too many skills ({len(skill_dirs)} > MAX_SKILLS={max_total_skills})",
                details={"count": len(skill_dirs), "max": max_total_skills},
            )
        )
    for skill_dir in skill_dirs:
        skill_md = skill_dir / "SKILL.md"
        size = skill_md.stat().st_size
        if size > max_skill_md_bytes:
            results.append(
                GateResult(
                    gate_id="skill_leanness",
                    passed=False,
                    severity="error",
                    message=f"{skill_dir}: SKILL.md too large ({size} bytes > {max_skill_md_bytes})",
                    details={"path": str(skill_md), "size": size, "max": max_skill_md_bytes},
                )
            )
    return results


def print_validation(results: list[GateResult]) -> int:
    failed = [result for result in results if not result.passed]
    if failed:
        print("REPO VALIDATION FAILED:")
        for result in failed:
            print(f"- [{result.gate_id}] {result.message}")
        return 1
    print("REPO VALIDATION PASSED")
    return 0
