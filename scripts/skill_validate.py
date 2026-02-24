#!/usr/bin/env python3
"""Validate SKILL.md files (New-knowledge base strict frontmatter + orchestration checks)."""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

from frontmatter import read_skill_md

MAX_SKILL_NAME_LENGTH = 64
ALLOWED_FRONTMATTER_KEYS = {"name", "description", "license", "allowed-tools", "metadata"}
NAME_RE = re.compile(r"^[a-z0-9-]+$")

@dataclass
class Skill:
    name: str
    description: str
    kind: str
    metadata: Dict[str, Any]
    dir: Path

def validate_skill_dir(skill_dir: Path, max_skill_md_bytes: int | None = None) -> Tuple[bool, str, Skill | None]:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return False, f"{skill_dir}: SKILL.md not found", None

    if max_skill_md_bytes is not None:
        sz = skill_md.stat().st_size
        if sz > max_skill_md_bytes:
            return False, f"{skill_dir}: SKILL.md too large ({sz} bytes > {max_skill_md_bytes})", None

    try:
        doc = read_skill_md(skill_dir)
    except Exception as e:
        return False, f"{skill_dir}: {e}", None

    fm = doc.frontmatter
    unexpected = set(fm.keys()) - ALLOWED_FRONTMATTER_KEYS
    if unexpected:
        return False, f"{skill_dir}: Unexpected frontmatter keys: {sorted(unexpected)}", None

    if "name" not in fm or "description" not in fm:
        return False, f"{skill_dir}: Frontmatter must include name + description", None

    name = fm["name"]
    desc = fm["description"]
    if not isinstance(name, str) or not isinstance(desc, str):
        return False, f"{skill_dir}: name/description must be strings", None

    name = name.strip()
    desc = desc.strip()

    if (not name or len(name) > MAX_SKILL_NAME_LENGTH or not NAME_RE.match(name)
        or "--" in name or name.startswith("-") or name.endswith("-")):
        return False, f"{skill_dir}: invalid name '{name}' (hyphen-case, <= {MAX_SKILL_NAME_LENGTH})", None

    if "<" in desc or ">" in desc or len(desc) > 1024:
        return False, f"{skill_dir}: invalid description (no angle brackets; <= 1024 chars)", None

    md = fm.get("metadata") or {}
    if md is None:
        md = {}
    if not isinstance(md, dict):
        return False, f"{skill_dir}: metadata must be a mapping", None

    kind = str(md.get("kind") or "other")
    return True, "OK", Skill(name=name, description=desc, kind=kind, metadata=md, dir=skill_dir)

def scan_skills(skills_root: Path) -> List[Path]:
    if not skills_root.exists():
        return []
    out = []
    for child in skills_root.iterdir():
        if child.is_dir() and (child / "SKILL.md").exists():
            out.append(child)
    return out

def validate_orchestration(skills: Dict[str, Skill]) -> List[str]:
    errors: List[str] = []
    procedures = {s.name for s in skills.values() if s.kind == "procedure"}
    playbooks = [s for s in skills.values() if s.kind == "playbook"]

    for pb in playbooks:
        steps = pb.metadata.get("steps")
        if not isinstance(steps, list) or not steps:
            errors.append(f"{pb.name}: playbook must have metadata.steps (non-empty list)")
            continue
        seen_calls: Set[str] = set()
        for idx, st in enumerate(steps):
            if not isinstance(st, dict) or "call" not in st:
                errors.append(f"{pb.name}: step {idx} must be mapping with 'call'")
                continue
            call = st["call"]
            if not isinstance(call, str):
                errors.append(f"{pb.name}: step {idx} call must be string")
                continue
            if call not in procedures:
                errors.append(f"{pb.name}: step {idx} calls unknown procedure '{call}'")
            if call in seen_calls:
                errors.append(f"{pb.name}: repeated procedure call '{call}' (cycle-like guard in MVP)")
            seen_calls.add(call)
    return errors

def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    skills_root = repo / "skills"

    max_skill_md_bytes = None
    raw = os.environ.get("MAX_SKILL_MD_BYTES")
    if raw:
        try:
            max_skill_md_bytes = int(raw)
        except ValueError:
            print("Invalid MAX_SKILL_MD_BYTES", file=sys.stderr)
            return 2

    skill_dirs = scan_skills(skills_root)
    if not skill_dirs:
        print("No skills found under ./skills (OK for early development).")
        return 0

    skills: Dict[str, Skill] = {}
    for d in skill_dirs:
        ok, msg, sk = validate_skill_dir(d, max_skill_md_bytes=max_skill_md_bytes)
        if not ok:
            print(f"VALIDATION FAILED: {msg}")
            return 1
        assert sk is not None
        if sk.name in skills:
            print(f"VALIDATION FAILED: duplicate skill name '{sk.name}' in {d}")
            return 1
        skills[sk.name] = sk

    errors = validate_orchestration(skills)
    if errors:
        print("VALIDATION FAILED:")
        for e in errors:
            print(f"- {e}")
        return 1

    print(f"VALIDATION PASSED: {len(skills)} skills")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
