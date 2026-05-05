from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import ValidationError

from evolvekb.assets.frontmatter import read_markdown, read_skill_md
from evolvekb.core.models import KnowledgeBlock, SkillAsset, UsageAsset


def _schema_for_type(type_name: Any) -> dict[str, Any]:
    if isinstance(type_name, dict):
        return type_name
    if not isinstance(type_name, str):
        return {"type": "object"}
    mapping = {
        "str": "string",
        "string": "string",
        "int": "integer",
        "float": "number",
        "bool": "boolean",
        "dict": "object",
        "list": "array",
    }
    return {"type": mapping.get(type_name, type_name)}


def normalize_schema_map(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {}
    return {str(key): _schema_for_type(value) for key, value in raw.items()}


def load_knowledge(path: Path) -> KnowledgeBlock:
    doc = read_markdown(path)
    fm = dict(doc.frontmatter)
    if fm.get("schema_version") == 2:
        return KnowledgeBlock(**fm)

    source = fm.get("source")
    migrated = {
        "schema_version": 2,
        "id": f"kb_{fm.get('name', path.stem).replace('-', '_')}",
        "name": fm.get("name", path.stem),
        "kind": "knowledge",
        "block_type": "reference",
        "source_refs": [{"source_id": str(source), "chunk_ids": []}] if source else [],
        "summary": fm.get("summary", ""),
        "claims": [],
        "concepts": fm.get("concepts") or [],
        "source_ids": [str(source)] if source else [],
        "chunk_ids": [],
        "confidence": 0.5,
        "updated_at": fm.get("updated_at"),
        "version": 1,
        "tags": [],
        "recommended_usage": [],
        "status": "active",
        "metadata": {"legacy_schema_version": 1, "source": source},
    }
    return KnowledgeBlock(**migrated)


def load_usage(path: Path) -> UsageAsset:
    doc = read_markdown(path)
    fm = dict(doc.frontmatter)
    if fm.get("kind") != "usage":
        raise ValueError(f"{path}: unsupported usage kind {fm.get('kind')!r}")
    if fm.get("schema_version") == 2:
        return UsageAsset(**fm)

    name = fm.get("name", path.stem)
    migrated = {
        "schema_version": 2,
        "id": f"usage_{str(name).replace('-', '_')}",
        "name": name,
        "kind": "usage",
        "intent": fm.get("intent", ""),
        "strategy": fm.get("strategy", "playbook"),
        "pattern": fm.get("pattern", "TBD"),
        "uses": fm.get("uses") or [],
        "playbook": name if fm.get("strategy") == "playbook" else None,
        "steps": fm.get("steps") or [],
        "trigger_examples": [],
        "anti_trigger_examples": [],
        "gate_policy_ids": [],
        "eval_case_ids": [],
        "updated_at": fm.get("updated_at"),
        "needs_review": bool(fm.get("needs_review", False)),
    }
    return UsageAsset(**migrated)


def load_skill(skill_dir: Path) -> SkillAsset:
    doc = read_skill_md(skill_dir)
    fm = dict(doc.frontmatter)
    metadata = fm.get("metadata") or {}
    if not isinstance(metadata, dict):
        raise ValueError(f"{skill_dir}: metadata must be a mapping")
    kind = metadata.get("kind")
    data = {
        "schema_version": fm.get("schema_version", 1),
        "name": fm.get("name"),
        "description": fm.get("description"),
        "kind": kind,
        "intent": metadata.get("intent"),
        "inputs_schema": normalize_schema_map(metadata.get("inputs")),
        "outputs_schema": normalize_schema_map(metadata.get("outputs")),
        "steps": metadata.get("steps") or [],
        "preconditions": metadata.get("preconditions") or [],
        "postconditions": metadata.get("postconditions") or [],
        "allowed_tools": fm.get("allowed-tools") or fm.get("allowed_tools") or [],
        "supporting_files": metadata.get("supporting_files") or [],
        "examples": metadata.get("examples") or [],
        "version": str(metadata.get("version") or "0.2.0"),
        "metadata": metadata,
    }
    try:
        return SkillAsset(**data)
    except ValidationError as exc:
        raise ValueError(f"{skill_dir}: {exc}") from exc
