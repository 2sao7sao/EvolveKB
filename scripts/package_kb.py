#!/usr/bin/env python3
"""Package skills directory into a distributable .kb zip (symlinks rejected)."""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

def package_kb(repo_root: Path, out_dir: Path) -> Path:
    skills_root = repo_root / "skills"
    if not skills_root.exists():
        raise SystemExit("skills/ not found")

    out_dir.mkdir(parents=True, exist_ok=True)
    kb_path = out_dir / "knowledge.kb"

    with zipfile.ZipFile(kb_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in skills_root.rglob("*"):
            if p.is_symlink():
                raise SystemExit(f"Symlinks are not allowed: {p}")
            if p.is_file():
                arc = p.relative_to(repo_root)
                z.write(p, arcname=str(arc))
    return kb_path

def main():
    repo_root = Path(__file__).resolve().parents[1]
    out_dir = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else (repo_root / "dist")
    kb = package_kb(repo_root, out_dir)
    print(f"OK: packaged -> {kb}")

if __name__ == "__main__":
    main()
