from __future__ import annotations

from pathlib import Path
from typing import Any

from evolvekb.core.models import SkillAsset


def run(
    *,
    repo: Path,
    skill: SkillAsset,
    env: dict[str, Any],
    args: dict[str, Any],
) -> str:
    question = str(args.get("question") or "")
    evidence = args.get("evidence") if isinstance(args.get("evidence"), dict) else {}
    items = evidence.get("items") or evidence.get("evidence") or []
    if not isinstance(items, list):
        items = []

    decision = _decide(question)
    evidence_rows = [
        item for item in items if isinstance(item, dict) and (item.get("asset_id") or item.get("name"))
    ]
    evidence_ids = [str(item.get("asset_id") or item.get("name")) for item in evidence_rows]
    source_refs = [str(item.get("source_ref")) for item in evidence_rows if item.get("source_ref")]

    lines = [
        "# Refund Decision",
        "",
        f"Question: {question}",
        f"Decision: {decision}",
        "",
        "## Evidence IDs",
    ]
    if evidence_ids:
        lines.extend(f"- {evidence_id}" for evidence_id in evidence_ids)
    else:
        lines.append("- none")

    lines.extend(["", "## Source Refs"])
    if source_refs:
        lines.extend(f"- {source_ref}" for source_ref in source_refs)
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Rationale",
            _rationale(decision),
        ]
    )
    return "\n".join(lines) + "\n"


def _decide(question: str) -> str:
    lower = question.lower()
    after_window = "45" in lower or "after 45" in lower or "after forty-five" in lower
    opened = "opened" in lower or "open box" in lower
    defective = "defective" in lower or "damaged" in lower
    if defective:
        return "eligible"
    if opened and after_window:
        return "needs_review"
    if "unopened" in lower and ("30" in lower or "within" in lower):
        return "eligible"
    return "needs_review"


def _rationale(decision: str) -> str:
    if decision == "eligible":
        return (
            "The request appears to match a supported refund path, but the agent "
            "must still cite the policy evidence above before finalizing."
        )
    if decision == "needs_review":
        return (
            "The request touches a policy boundary, so the agent should escalate "
            "with the cited evidence instead of inventing an approval."
        )
    return "The request is not supported by the available policy evidence."
