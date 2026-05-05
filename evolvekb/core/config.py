from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator


KnowledgeMode = Literal["reference", "digest", "transform", "evolve"]
OutputTemplate = Literal["compact", "expanded"]


class Settings(BaseModel):
    knowledge_mode: KnowledgeMode = "reference"
    gate_level: int = Field(default=1, ge=0, le=3)
    auto_evolve: bool = False
    max_skill_md_bytes: int = Field(default=50000, gt=0)
    output_template: OutputTemplate = "expanded"
    retrieval: dict[str, Any] = Field(default_factory=dict)
    proposal: dict[str, Any] = Field(default_factory=dict)
    gates: dict[str, Any] = Field(default_factory=dict)

    @field_validator("gate_level", mode="before")
    @classmethod
    def coerce_gate_level(cls, value: Any) -> int:
        return int(value)


def resolve_repo_path(repo: Path, path: str | Path | None) -> Path | None:
    if path is None:
        return None
    p = Path(path)
    return p if p.is_absolute() else repo / p


def load_settings(repo: Path, settings_arg: str | Path | None = None) -> Settings:
    data: dict[str, Any] = {}
    if settings_arg:
        p = resolve_repo_path(repo, settings_arg)
        assert p is not None
        if not p.exists():
            raise FileNotFoundError(f"Settings file not found: {p}")
        raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        if not isinstance(raw, dict):
            raise ValueError("Settings YAML must be a mapping/dict at top level")
        data.update(raw)
    try:
        return Settings(**data)
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc
