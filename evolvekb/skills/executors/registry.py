from __future__ import annotations

from evolvekb.skills.executors.base import ProcedureExecutor
from evolvekb.skills.executors.python import PythonProcedureExecutor


def get_executor(kind: str | None) -> ProcedureExecutor:
    runtime_kind = (kind or "").strip().lower()
    if runtime_kind == "python":
        return PythonProcedureExecutor()
    raise ValueError(f"Unknown procedure runtime '{kind}'. Expected one of: python")
