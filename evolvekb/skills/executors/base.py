from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from evolvekb.core.models import SkillAsset


class ProcedureExecutor(Protocol):
    kind: str

    def execute(
        self,
        *,
        repo: Path,
        skill: SkillAsset,
        env: dict[str, Any],
        args: dict[str, Any],
    ) -> Any:
        ...
