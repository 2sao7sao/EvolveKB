#!/usr/bin/env python3
"""Repo validation runner (wraps skill validation + leanness checks)."""

from __future__ import annotations
import os
import sys
from pathlib import Path
import subprocess

def main() -> int:
    repo = Path(__file__).resolve().parents[1]

    # Gate: skills
    r = subprocess.run([sys.executable, str(repo / "scripts" / "skill_validate.py")])
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
