#!/usr/bin/env python3
"""Legacy wrapper for `evolvekb run`."""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evolvekb.cli import legacy_run_main
from evolvekb.skills.runtime import (
    build_comparison_axes,
    compose_answer_md,
    compose_knowledge_md,
    compose_skill_draft,
    contrast_matrix,
    eval_value,
    extract_outline,
    normalize_question,
    render_by_mode,
)

__all__ = [
    "build_comparison_axes",
    "compose_answer_md",
    "compose_knowledge_md",
    "compose_skill_draft",
    "contrast_matrix",
    "eval_value",
    "extract_outline",
    "normalize_question",
    "render_by_mode",
]


if __name__ == "__main__":
    raise SystemExit(legacy_run_main())
