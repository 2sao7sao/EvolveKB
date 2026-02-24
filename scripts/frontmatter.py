from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import yaml

FRONT_RE = re.compile(r"^---\n(.*?)\n---\n?", re.DOTALL)

@dataclass
class FrontmatterDoc:
    frontmatter: Dict[str, Any]
    body: str

def parse_frontmatter(text: str) -> FrontmatterDoc:
    if not text.startswith("---"):
        raise ValueError("No YAML frontmatter found (expected leading ---)")
    m = FRONT_RE.match(text)
    if not m:
        raise ValueError("Invalid frontmatter format")
    fm_text = m.group(1)
    fm = yaml.safe_load(fm_text)
    if not isinstance(fm, dict):
        raise ValueError("Frontmatter must be a YAML dictionary")
    body = text[m.end():]
    return FrontmatterDoc(frontmatter=fm, body=body)

def read_skill_md(skill_dir: Path) -> FrontmatterDoc:
    p = skill_dir / "SKILL.md"
    if not p.exists():
        raise FileNotFoundError("SKILL.md not found")
    return parse_frontmatter(p.read_text(encoding="utf-8"))
