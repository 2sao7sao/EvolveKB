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
    with zipfile.ZipFile(kb_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in skills_root.rglob("*"):
            if path.is_symlink():
                raise SystemExit(f"Symlinks are not allowed: {path}")
            if path.is_file():
                archive.write(path, arcname=str(path.relative_to(repo_root)))
    return kb_path


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    repo_root = Path.cwd()
    out_dir = Path(argv[0]).resolve() if argv else repo_root / "dist"
    kb = package_kb(repo_root, out_dir)
    print(f"OK: packaged -> {kb}")
    return 0
