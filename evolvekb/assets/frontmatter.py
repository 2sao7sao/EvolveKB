from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

FRONT_RE = re.compile(r"^---\n(.*?)\n---\n?", re.DOTALL)


@dataclass
class FrontmatterDoc:
    frontmatter: dict[str, Any]
    body: str


def parse_frontmatter(text: str) -> FrontmatterDoc:
    if not text.startswith("---"):
        raise ValueError("No YAML frontmatter found (expected leading ---)")
    match = FRONT_RE.match(text)
    if not match:
        raise ValueError("Invalid frontmatter format")
    fm = yaml.safe_load(match.group(1))
    if not isinstance(fm, dict):
        raise ValueError("Frontmatter must be a YAML dictionary")
    return FrontmatterDoc(frontmatter=fm, body=text[match.end() :])


def read_markdown(path: Path) -> FrontmatterDoc:
    return parse_frontmatter(path.read_text(encoding="utf-8"))


def read_skill_md(skill_dir: Path) -> FrontmatterDoc:
    path = skill_dir / "SKILL.md"
    if not path.exists():
        raise FileNotFoundError("SKILL.md not found")
    return read_markdown(path)


def dump_frontmatter(frontmatter: dict[str, Any], body: str) -> str:
    fm = yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True).strip()
    return f"---\n{fm}\n---\n{body}"
