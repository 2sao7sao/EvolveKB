from __future__ import annotations

import os
import json
import re
from pathlib import Path

from evolvekb.assets.frontmatter import parse_frontmatter
from evolvekb.assets.registry import AssetRegistry
from evolvekb.core.config import load_settings
from evolvekb.core.models import GateResult


def validate_repo(repo: Path, settings_arg: str | Path | None = None) -> list[GateResult]:
    settings = load_settings(repo, settings_arg)
    registry = AssetRegistry.load(repo)
    results = registry.validation_results(settings.gate_level)
    results.extend(validate_leanness(repo, settings.max_skill_md_bytes))
    results.extend(validate_claim_evidence(repo))
    results.extend(validate_proposal_metadata(repo))
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


def _normalize_evidence(text: str) -> str:
    """Compare quotes with chunk text regardless of markdown and whitespace noise."""
    stripped = re.sub(r"[*_\x60]{1,3}", "", str(text))
    return re.sub(r"\s+", "", stripped).lower()


def _load_chunk_text(repo: Path) -> dict[str, str] | None:
    """Chunk id -> normalized text, or None when the repository has no chunk store."""
    chunks_root = repo / "kb" / "chunks"
    if not chunks_root.exists():
        return None
    chunks: dict[str, str] = {}
    for path in sorted(chunks_root.glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            chunk_id = str(row.get("id") or "")
            if chunk_id:
                chunks[chunk_id] = _normalize_evidence(row.get("text") or "")
    return chunks


def quote_matches_chunks(repo: Path, chunk_ids: list[str] | tuple[str, ...], quote: str) -> bool | None:
    """Whether a quote appears in one of its chunks; None when no chunk store exists."""
    chunks = _load_chunk_text(repo)
    if chunks is None:
        return None
    normalized = _normalize_evidence(quote)
    return any(str(chunk_id) in chunks and normalized in chunks[str(chunk_id)] for chunk_id in chunk_ids)


def validate_claim_evidence(repo: Path) -> list[GateResult]:
    results: list[GateResult] = []
    claims_root = repo / "kb" / "claims"
    if not claims_root.exists():
        return results
    chunks = _load_chunk_text(repo)
    for path in sorted(claims_root.glob("*.jsonl")):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("status", "active") != "active":
                continue
            quote = str(row.get("evidence_quote") or "").strip()
            if not quote:
                results.append(
                    GateResult(
                        gate_id="claim_has_evidence_quote",
                        passed=False,
                        severity="blocker",
                        message=f"{path.relative_to(repo)}:{line_number}: active claim missing evidence_quote",
                        details={"path": str(path.relative_to(repo)), "line": line_number},
                    )
                )
                continue
            # A quote that does not appear in its own chunk is fabricated evidence.
            if chunks is not None:
                normalized = _normalize_evidence(quote)
                chunk_ids = [str(cid) for cid in (row.get("chunk_ids") or [])]
                found = any(
                    chunk_id in chunks and normalized in chunks[chunk_id]
                    for chunk_id in chunk_ids
                )
                if not found:
                    results.append(
                        GateResult(
                            gate_id="claim_evidence_quote_matches_chunk",
                            passed=False,
                            severity="blocker",
                            message=(
                                f"{path.relative_to(repo)}:{line_number}: evidence_quote not found in "
                                f"referenced chunk(s) {chunk_ids}"
                            ),
                            details={"path": str(path.relative_to(repo)), "line": line_number,
                                     "chunk_ids": chunk_ids},
                        )
                    )
    return results


def validate_proposal_metadata(repo: Path) -> list[GateResult]:
    results: list[GateResult] = []
    proposals_root = repo / "kb" / "proposals"
    if not proposals_root.exists():
        return results
    for path in sorted(proposals_root.glob("*.md")):
        doc = parse_frontmatter(path.read_text(encoding="utf-8"))
        fm = dict(doc.frontmatter)
        impact = fm.get("impact") if isinstance(fm.get("impact"), dict) else {}
        rollback_plan = impact.get("rollback_plan") if isinstance(impact.get("rollback_plan"), dict) else {}
        impacted_assets = fm.get("impacted_assets") or []
        impacted_eval_ids = impact.get("impacted_eval_ids") or []
        if not impact or not impacted_assets:
            results.append(
                GateResult(
                    gate_id="proposal_has_impact_summary",
                    passed=False,
                    severity="blocker",
                    message=f"{path.relative_to(repo)}: proposal missing impact summary or impacted assets",
                    details={"path": str(path.relative_to(repo))},
                )
            )
        if not rollback_plan.get("files") or "before_hashes" not in rollback_plan:
            results.append(
                GateResult(
                    gate_id="proposal_has_rollback_plan",
                    passed=False,
                    severity="blocker",
                    message=f"{path.relative_to(repo)}: proposal missing rollback plan files or hashes",
                    details={"path": str(path.relative_to(repo))},
                )
            )
        if impacted_assets and not impacted_eval_ids:
            results.append(
                GateResult(
                    gate_id="proposal_impacted_evals_declared",
                    passed=True,
                    severity="warning",
                    message=f"{path.relative_to(repo)}: no impacted evals declared",
                    details={"path": str(path.relative_to(repo))},
                )
            )
    return results


def print_validation(results: list[GateResult]) -> int:
    failed = [result for result in results if not result.passed]
    total = len(results)
    passed_count = total - len(failed)
    if failed:
        print(f"REPO VALIDATION FAILED: {passed_count}/{total} passed, {len(failed)} failed")
        for result in failed:
            print(f"- [{result.gate_id}] {result.message}")
        return 1
    if total:
        print(f"REPO VALIDATION PASSED: {total}/{total} passed")
    else:
        print("REPO VALIDATION PASSED: no gates evaluated (clean repo, no kb/claims or kb/proposals to scan)")
    return 0
