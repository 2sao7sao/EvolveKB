from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from evolvekb.assets.registry import AssetRegistry


@dataclass
class LintIssue:
    code: str
    message: str
    path: str


def rebuild_kb_index(repo: Path) -> Path:
    registry = AssetRegistry.load(repo)
    out = repo / "kb" / "index.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    lines = [
        "---",
        "schema_version: 2",
        "kind: kb-index",
        f"updated_at: {now}",
        "---",
        "",
        "# EvolveKB Index",
        "",
        "## Knowledge",
    ]
    for item in sorted(registry.knowledge.values(), key=lambda asset: asset.name):
        concepts = ", ".join(item.concepts[:5]) if item.concepts else "no concepts"
        lines.append(f"- [[knowledge/{item.name}]] — {item.summary} _(concepts: {concepts})_")

    lines.extend(["", "## Usage"])
    for item in sorted(registry.usage.values(), key=lambda asset: asset.name):
        uses = ", ".join(item.uses) if item.uses else "none"
        lines.append(f"- [[usage/{item.name}]] — intent `{item.intent}`, pattern `{item.pattern}`, uses: {uses}")

    lines.extend(["", "## Skills"])
    for item in sorted(registry.skills.values(), key=lambda asset: asset.name):
        intent = f", intent `{item.intent}`" if item.intent else ""
        lines.append(f"- [[../skills/{item.name}/SKILL]] — `{item.kind}`{intent}, version `{item.version}`")

    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    append_kb_log(repo, "index", "Rebuilt kb/index.md")
    return out


def append_kb_log(repo: Path, event_type: str, message: str) -> Path:
    out = repo / "kb" / "log.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if not out.exists():
        out.write_text("# EvolveKB Log\n\n", encoding="utf-8")
    with out.open("a", encoding="utf-8") as handle:
        handle.write(f"## [{now}] {event_type} | {message}\n\n")
    return out


def lint_kb(repo: Path, gate_level: int = 2) -> list[LintIssue]:
    registry = AssetRegistry.load(repo)
    issues: list[LintIssue] = []
    for result in registry.failed_results(gate_level=gate_level):
        issues.append(LintIssue(code=result.gate_id, message=result.message, path="kb"))

    usage_refs: dict[str, int] = {name: 0 for name in registry.knowledge}
    for usage in registry.usage.values():
        for ref in usage.uses:
            if ref in usage_refs:
                usage_refs[ref] += 1
    for name, count in sorted(usage_refs.items()):
        if count == 0:
            issues.append(
                LintIssue(
                    code="orphan_knowledge",
                    message=f"knowledge '{name}' is not referenced by any usage asset",
                    path=f"kb/knowledge/{name}.md",
                )
            )

    for usage in registry.usage.values():
        if usage.playbook and usage.playbook not in registry.skills:
            issues.append(
                LintIssue(
                    code="missing_playbook",
                    message=f"usage '{usage.name}' points to missing playbook '{usage.playbook}'",
                    path=f"kb/usage/{usage.name}.md",
                )
            )
    return issues
