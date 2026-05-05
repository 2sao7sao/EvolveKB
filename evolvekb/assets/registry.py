from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from evolvekb.assets.hashing import file_hash, stable_hash
from evolvekb.assets.loader import load_knowledge, load_skill, load_usage
from evolvekb.core.models import GateResult, KnowledgeBlock, SkillAsset, UsageAsset


@dataclass
class AssetRegistry:
    repo: Path
    knowledge: dict[str, KnowledgeBlock] = field(default_factory=dict)
    usage: dict[str, UsageAsset] = field(default_factory=dict)
    skills: dict[str, SkillAsset] = field(default_factory=dict)
    asset_hashes: dict[str, str] = field(default_factory=dict)
    load_errors: list[str] = field(default_factory=list)

    @classmethod
    def load(cls, repo: Path) -> "AssetRegistry":
        registry = cls(repo=repo)
        registry._load_knowledge()
        registry._load_usage()
        registry._load_skills()
        return registry

    def _record_hash(self, key: str, path: Path, value: Any) -> None:
        self.asset_hashes[key] = file_hash(path) if path.exists() else stable_hash(value)

    def _load_knowledge(self) -> None:
        root = self.repo / "kb" / "knowledge"
        if not root.exists():
            return
        for path in sorted(root.glob("*.md")):
            try:
                asset = load_knowledge(path)
                if asset.name in self.knowledge:
                    self.load_errors.append(f"{path}: duplicate knowledge name '{asset.name}'")
                self.knowledge[asset.name] = asset
                self._record_hash(f"knowledge:{asset.name}", path, asset.model_dump())
            except (ValueError, ValidationError) as exc:
                self.load_errors.append(str(exc))

    def _load_usage(self) -> None:
        root = self.repo / "kb" / "usage"
        if not root.exists():
            return
        for path in sorted(root.glob("*.md")):
            if path.name == "index.md":
                continue
            try:
                asset = load_usage(path)
                if asset.name in self.usage:
                    self.load_errors.append(f"{path}: duplicate usage name '{asset.name}'")
                self.usage[asset.name] = asset
                self._record_hash(f"usage:{asset.name}", path, asset.model_dump())
            except (ValueError, ValidationError) as exc:
                self.load_errors.append(str(exc))

    def _load_skills(self) -> None:
        root = self.repo / "skills"
        if not root.exists():
            return
        for skill_dir in sorted(p for p in root.iterdir() if p.is_dir()):
            if not (skill_dir / "SKILL.md").exists():
                continue
            try:
                asset = load_skill(skill_dir)
                if asset.name in self.skills:
                    self.load_errors.append(f"{skill_dir}: duplicate skill name '{asset.name}'")
                self.skills[asset.name] = asset
                self._record_hash(f"skill:{asset.name}", skill_dir / "SKILL.md", asset.model_dump())
            except (ValueError, ValidationError) as exc:
                self.load_errors.append(str(exc))

    def validation_results(self, gate_level: int = 1) -> list[GateResult]:
        results: list[GateResult] = []
        for err in self.load_errors:
            results.append(
                GateResult(
                    gate_id="asset_load",
                    passed=False,
                    severity="blocker",
                    message=err,
                    details={},
                )
            )

        results.extend(self._validate_unique_ids())
        results.extend(self._validate_skills(gate_level))
        results.extend(self._validate_usage_refs(gate_level))
        return results

    def _validate_unique_ids(self) -> list[GateResult]:
        seen: dict[str, str] = {}
        results: list[GateResult] = []
        for prefix, assets in (("knowledge", self.knowledge), ("usage", self.usage)):
            for name, asset in assets.items():
                asset_id = asset.id
                if asset_id in seen:
                    results.append(
                        GateResult(
                            gate_id="asset_unique_id",
                            passed=False,
                            severity="blocker",
                            message=f"duplicate asset id '{asset_id}' in {seen[asset_id]} and {prefix}:{name}",
                            details={"asset_id": asset_id},
                        )
                    )
                seen[asset_id] = f"{prefix}:{name}"
        return results

    def _validate_skills(self, gate_level: int) -> list[GateResult]:
        results: list[GateResult] = []
        procedures = {name for name, s in self.skills.items() if s.kind == "procedure"}
        for skill in self.skills.values():
            if skill.kind == "playbook":
                if not skill.steps:
                    results.append(
                        GateResult(
                            gate_id="playbook_orchestration",
                            passed=False,
                            severity="blocker",
                            message=f"{skill.name}: playbook must define metadata.steps",
                            details={"skill": skill.name},
                        )
                    )
                for idx, step in enumerate(skill.steps):
                    call = step.get("call") if isinstance(step, dict) else None
                    if not isinstance(call, str):
                        results.append(
                            GateResult(
                                gate_id="playbook_orchestration",
                                passed=False,
                                severity="blocker",
                                message=f"{skill.name}: step {idx} must define call",
                                details={"skill": skill.name, "step_index": idx},
                            )
                        )
                    elif call not in procedures:
                        results.append(
                            GateResult(
                                gate_id="playbook_orchestration",
                                passed=False,
                                severity="blocker",
                                message=f"{skill.name}: step {idx} calls unknown procedure '{call}'",
                                details={"skill": skill.name, "step_index": idx, "call": call},
                            )
                        )
            if gate_level >= 2 and skill.kind == "procedure":
                if not skill.inputs_schema:
                    results.append(
                        GateResult(
                            gate_id="procedure_contract",
                            passed=False,
                            severity="error",
                            message=f"{skill.name}: procedure must define inputs at gate>=2",
                            details={"skill": skill.name},
                        )
                    )
                if not skill.outputs_schema:
                    results.append(
                        GateResult(
                            gate_id="procedure_contract",
                            passed=False,
                            severity="error",
                            message=f"{skill.name}: procedure must define outputs at gate>=2",
                            details={"skill": skill.name},
                        )
                    )
        return results

    def _validate_usage_refs(self, gate_level: int) -> list[GateResult]:
        if gate_level < 2:
            return []
        results: list[GateResult] = []
        knowledge_names = set(self.knowledge)
        for usage in self.usage.values():
            if "TBD" in usage.uses:
                results.append(
                    GateResult(
                        gate_id="usage_reference_resolution",
                        passed=False,
                        severity="error",
                        message=f"{usage.name}: uses cannot include TBD at gate>=2",
                        details={"usage": usage.name},
                    )
                )
            for ref in usage.uses:
                if ref != "TBD" and ref not in knowledge_names:
                    results.append(
                        GateResult(
                            gate_id="usage_reference_resolution",
                            passed=False,
                            severity="error",
                            message=f"{usage.name}: uses unknown knowledge '{ref}'",
                            details={"usage": usage.name, "ref": ref},
                        )
                    )
            if usage.playbook and usage.playbook not in self.skills:
                results.append(
                    GateResult(
                        gate_id="usage_playbook_resolution",
                        passed=False,
                        severity="error",
                        message=f"{usage.name}: playbook '{usage.playbook}' does not exist",
                        details={"usage": usage.name, "playbook": usage.playbook},
                    )
                )
        return results

    def failed_results(self, gate_level: int = 1) -> list[GateResult]:
        return [r for r in self.validation_results(gate_level) if not r.passed]
