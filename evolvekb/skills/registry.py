from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from evolvekb.assets.registry import AssetRegistry
from evolvekb.core.models import SkillAsset


@dataclass
class SkillRegistry:
    assets: dict[str, SkillAsset]

    @classmethod
    def load(cls, repo: Path) -> "SkillRegistry":
        return cls(AssetRegistry.load(repo).skills)

    def pick_playbook(self, intent: str) -> SkillAsset:
        direct = self.assets.get(intent)
        if direct and direct.kind == "playbook":
            return direct
        for skill in self.assets.values():
            if skill.kind == "playbook" and skill.intent == intent:
                return skill
        raise KeyError(f"No playbook for intent: {intent}")

    def list(self) -> list[SkillAsset]:
        return sorted(self.assets.values(), key=lambda s: s.name)

    def inspect(self, name: str) -> SkillAsset:
        if name not in self.assets:
            raise KeyError(f"Unknown skill: {name}")
        return self.assets[name]
