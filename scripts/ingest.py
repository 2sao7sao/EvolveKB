#!/usr/bin/env python3
"""Ingest a markdown document and generate a knowledge asset."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from frontmatter import parse_frontmatter

# Import helpers from run.py (deterministic placeholder implementations)
from run import extract_outline, compose_knowledge_md


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc", required=True, help="Path to a markdown document")
    ap.add_argument("--out", default=None, help="Output knowledge directory (default: repo/kb/knowledge)")
    ap.add_argument("--force", action="store_true", help="Overwrite existing knowledge file")
    args = ap.parse_args()

    repo = Path(__file__).resolve().parents[1]
    doc_path = Path(args.doc)
    if not doc_path.is_absolute():
        doc_path = repo / doc_path

    outline = extract_outline(str(doc_path))
    knowledge_md = compose_knowledge_md(outline)
    fm = parse_frontmatter(knowledge_md)
    name = fm.frontmatter.get("name")
    if not name:
        print("Failed to parse knowledge name from generated draft", file=sys.stderr)
        return 2

    kb_root = Path(args.out) if args.out else repo / "kb" / "knowledge"
    if not kb_root.is_absolute():
        kb_root = repo / kb_root

    kb_root.mkdir(parents=True, exist_ok=True)
    out_path = kb_root / f"{name}.md"
    if out_path.exists() and not args.force:
        print(f"Knowledge already exists: {out_path}. Use --force to overwrite.", file=sys.stderr)
        return 1

    out_path.write_text(knowledge_md, encoding="utf-8")

    print(f"[ingest] wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
