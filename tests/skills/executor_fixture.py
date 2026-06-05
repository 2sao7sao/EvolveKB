from __future__ import annotations

from pathlib import Path
from typing import Any

from evolvekb.core.models import SkillAsset


def run(
    *,
    repo: Path,
    skill: SkillAsset,
    env: dict[str, Any],
    args: dict[str, Any],
) -> str:
    return f"# Echo\n\n{args['text']}"
