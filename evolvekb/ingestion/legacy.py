from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from evolvekb.assets.frontmatter import parse_frontmatter
from evolvekb.skills.runtime import compose_knowledge_md, extract_outline
from evolvekb.wiki import append_kb_log


def ingest_markdown(repo: Path, doc: str, out: str | None = None, force: bool = False) -> Path:
    doc_path = Path(doc)
    if not doc_path.is_absolute():
        doc_path = repo / doc_path

    outline = extract_outline(str(doc_path))
    knowledge_md = compose_knowledge_md(outline)
    parsed = parse_frontmatter(knowledge_md)
    name = parsed.frontmatter.get("name")
    if not name:
        raise ValueError("Failed to parse knowledge name from generated draft")

    kb_root = Path(out) if out else repo / "kb" / "knowledge"
    if not kb_root.is_absolute():
        kb_root = repo / kb_root
    kb_root.mkdir(parents=True, exist_ok=True)

    out_path = kb_root / f"{name}.md"
    if out_path.exists() and not force:
        raise FileExistsError(f"Knowledge already exists: {out_path}. Use --force to overwrite.")

    existed = out_path.exists()
    out_path.write_text(knowledge_md, encoding="utf-8")
    if existed:
        mark_related_usage_for_review(repo, str(name))
    append_kb_log(repo, "ingest", f"Generated knowledge asset {out_path.relative_to(repo) if out_path.is_relative_to(repo) else out_path}")
    return out_path


def mark_related_usage_for_review(repo: Path, name: str) -> None:
    usage_dir = repo / "kb" / "usage"
    if not usage_dir.exists():
        return
    for path in usage_dir.glob("*.md"):
        try:
            text = path.read_text(encoding="utf-8")
            if f"- {name}" in text or f"uses: [{name}]" in text:
                if "needs_review:" in text:
                    text = text.replace("needs_review: false", "needs_review: true")
                else:
                    text = text.replace("---\n", "---\nneeds_review: true\n", 1)
                path.write_text(text, encoding="utf-8")
        except Exception:
            continue


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--doc", required=True, help="Path to a markdown document")
    parser.add_argument("--out", default=None, help="Output knowledge directory (default: repo/kb/knowledge)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing knowledge file")
    args = parser.parse_args(argv)

    repo = Path.cwd()
    try:
        out_path = ingest_markdown(repo, args.doc, args.out, args.force)
    except FileExistsError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(f"[ingest] wrote {out_path}")
    return 0
