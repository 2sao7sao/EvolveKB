from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, Callable

from evolvekb.core.models import SkillAsset


class PythonProcedureExecutor:
    kind = "python"

    def execute(
        self,
        *,
        repo: Path,
        skill: SkillAsset,
        env: dict[str, Any],
        args: dict[str, Any],
    ) -> Any:
        entrypoint = str(skill.runtime.get("entrypoint") or "")
        if not entrypoint:
            raise ValueError(f"{skill.name}: python runtime requires runtime.entrypoint")
        target = _load_entrypoint(entrypoint)
        return target(repo=repo, skill=skill, env=env, args=args)


def _load_entrypoint(entrypoint: str) -> Callable[..., Any]:
    if ":" not in entrypoint:
        raise ValueError(f"invalid python entrypoint '{entrypoint}', expected module:function")
    module_name, function_name = entrypoint.split(":", 1)
    if not module_name or not function_name:
        raise ValueError(f"invalid python entrypoint '{entrypoint}', expected module:function")
    module = importlib.import_module(module_name)
    target = getattr(module, function_name, None)
    if not callable(target):
        raise ValueError(f"python entrypoint '{entrypoint}' is not callable")
    return target
