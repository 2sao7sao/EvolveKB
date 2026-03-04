#!/usr/bin/env python3
"""Validate kb/knowledge and kb/usage assets."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from frontmatter import parse_frontmatter

NAME_RE = re.compile(r"^[a-z0-9-]+$")


def load_md(path: Path) -> Tuple[Dict[str, Any], str]:
    doc = parse_frontmatter(path.read_text(encoding="utf-8"))
    return doc.frontmatter, doc.body


def validate_knowledge(path: Path, fm: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    name = fm.get("name")
    if not isinstance(name, str) or not NAME_RE.match(name):
        errors.append(f"{path}: invalid name")
    if fm.get("kind") != "knowledge":
        errors.append(f"{path}: kind must be 'knowledge'")
    for key in ["source", "summary", "concepts", "updated_at"]:
        if key not in fm:
            errors.append(f"{path}: missing '{key}'")
    if "concepts" in fm and not isinstance(fm.get("concepts"), list):
        errors.append(f"{path}: concepts must be a list")
    return errors


def validate_usage(path: Path, fm: Dict[str, Any], knowledge_names: set[str]) -> List[str]:
    errors: List[str] = []
    name = fm.get("name")
    if not isinstance(name, str) or not NAME_RE.match(name):
        errors.append(f"{path}: invalid name")
    if fm.get("kind") != "usage":
        errors.append(f"{path}: kind must be 'usage'")
    uses = fm.get("uses")
    if not isinstance(uses, list) or not uses:
        errors.append(f"{path}: uses must be a non-empty list")
    else:
        for u in uses:
            if u not in knowledge_names:
                errors.append(f"{path}: uses unknown knowledge '{u}'")
    steps = fm.get("steps")
    if not isinstance(steps, list):
        errors.append(f"{path}: steps must be a list")
    return errors


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    kb = repo / "kb"
    knowledge_dir = kb / "knowledge"
    usage_dir = kb / "usage"

    if not kb.exists():
        print("KB VALIDATION PASSED: no kb directory")
        return 0

    errors: List[str] = []
    knowledge_names: set[str] = set()

    if knowledge_dir.exists():
        for p in sorted(knowledge_dir.glob("*.md")):
            fm, _ = load_md(p)
            name = fm.get("name")
            if isinstance(name, str):
                knowledge_names.add(name)
            errors.extend(validate_knowledge(p, fm))

    if usage_dir.exists():
        for p in sorted(usage_dir.glob("*.md")):
            fm, _ = load_md(p)
            errors.extend(validate_usage(p, fm, knowledge_names))

    if errors:
        print("KB VALIDATION FAILED:")
        for e in errors:
            print(f"- {e}")
        return 1

    print("KB VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
