#!/usr/bin/env python3
"""Repo validation runner (wraps skill validation + leanness checks)."""

from __future__ import annotations
import os
import sys
from pathlib import Path
import subprocess
import argparse
import yaml

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--settings", default=None, help="Path to settings YAML (e.g. settings/default.yaml)")
    args = ap.parse_args()

    repo = Path(__file__).resolve().parents[1]
    gate_level = 1
    max_skill_md_bytes = None
    if args.settings:
        p = Path(args.settings)
        if not p.is_absolute():
            p = repo / p
        if not p.exists():
            print(f"Settings file not found: {p}", file=sys.stderr)
            return 2
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        if isinstance(data, dict):
            gate_level = int(data.get("gate_level", gate_level))
            max_skill_md_bytes = data.get("max_skill_md_bytes")
        if max_skill_md_bytes is not None:
            os.environ["MAX_SKILL_MD_BYTES"] = str(max_skill_md_bytes)

    # Gate: skills
    r = subprocess.run([sys.executable, str(repo / "scripts" / "skill_validate.py"), "--gate-level", str(gate_level)])
    if r.returncode != 0:
        return r.returncode

    # Gate: knowledge base assets
    r = subprocess.run([sys.executable, str(repo / "scripts" / "kb_validate.py")])
    if r.returncode != 0:
        return r.returncode

    # Gate: leanness (soft limits)
    max_total_skills = int(os.environ.get("MAX_SKILLS", "500"))
    skills_root = repo / "skills"
    if skills_root.exists():
        count = sum(1 for p in skills_root.iterdir() if p.is_dir() and (p / "SKILL.md").exists())
        if count > max_total_skills:
            print(f"VALIDATION FAILED: too many skills ({count} > MAX_SKILLS={max_total_skills})")
            return 1

    print("REPO VALIDATION PASSED")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
