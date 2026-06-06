from __future__ import annotations

from pathlib import Path
import textwrap

import pytest

from evolvekb.core.models import SkillAsset
from evolvekb.skills.executors.python import PythonProcedureExecutor
from evolvekb.skills.registry import SkillRegistry
from evolvekb.skills.runtime import PlaybookRuntime


REPO = Path(__file__).resolve().parents[2]


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text).lstrip(), encoding="utf-8")


def test_python_executor_invokes_runtime_entrypoint() -> None:
    skill = SkillAsset(
        name="custom-entrypoint",
        description="Custom test procedure",
        kind="procedure",
        runtime={
            "type": "python",
            "entrypoint": "tests.skills.executor_fixture:run",
            "side_effects": False,
        },
    )

    result = PythonProcedureExecutor().execute(
        repo=REPO,
        skill=skill,
        env={"settings": {}},
        args={"text": "hello"},
    )

    assert result == "# Echo\n\nhello"


def test_skill_loader_reads_runtime_metadata() -> None:
    skill = SkillRegistry.load(REPO).inspect("retrieve-evidence")
    assert skill.runtime["type"] == "python"
    assert skill.runtime["entrypoint"] == "evolvekb.procedures.retrieve_evidence:run"


def test_runtime_runs_entrypoint_procedure_without_proc_impl(tmp_path: Path) -> None:
    write(
        tmp_path / "skills" / "custom-playbook" / "SKILL.md",
        """
        ---
        schema_version: 2
        name: custom-playbook
        description: Run a custom entrypoint-backed procedure.
        allowed-tools: []
        metadata:
          kind: playbook
          intent: custom_entrypoint
          steps:
            - call: custom-entrypoint
              in:
                text: $inputs.question
              out: $outputs.answer_md
          version: 0.3.0
        ---

        # custom-playbook
        """,
    )
    write(
        tmp_path / "skills" / "custom-entrypoint" / "SKILL.md",
        """
        ---
        schema_version: 2
        name: custom-entrypoint
        description: Echo the provided text through a Python entrypoint.
        allowed-tools: []
        metadata:
          kind: procedure
          inputs:
            text: str
          outputs:
            answer_md: str
          runtime:
            type: python
            entrypoint: tests.skills.executor_fixture:run
            side_effects: false
          version: 0.3.0
        ---

        # custom-entrypoint
        """,
    )

    result = PlaybookRuntime(tmp_path).run(
        intent="custom_entrypoint",
        question="hello",
        write_side_effects=False,
    )

    assert result.rendered == "# Echo\n\nhello"
    assert result.trace.selected_skill == "custom-playbook"
    assert [step.procedure for step in result.trace.step_traces] == ["custom-entrypoint"]
    assert result.trace.step_traces[0].success is True


def test_runtime_blocks_side_effect_entrypoint_when_disabled(tmp_path: Path) -> None:
    write(
        tmp_path / "skills" / "side-effect-playbook" / "SKILL.md",
        """
        ---
        schema_version: 2
        name: side-effect-playbook
        description: Run a side-effect-backed procedure.
        allowed-tools: []
        metadata:
          kind: playbook
          intent: side_effect_entrypoint
          steps:
            - call: side-effect-entrypoint
              in:
                text: $inputs.question
              out: $outputs.answer_md
          version: 0.3.0
        ---

        # side-effect-playbook
        """,
    )
    write(
        tmp_path / "skills" / "side-effect-entrypoint" / "SKILL.md",
        """
        ---
        schema_version: 2
        name: side-effect-entrypoint
        description: Side-effect procedure used to verify no-side-effects policy.
        allowed-tools: []
        metadata:
          kind: procedure
          inputs:
            text: str
          outputs:
            answer_md: str
          runtime:
            type: python
            entrypoint: tests.skills.executor_fixture:run
            side_effects: true
          version: 0.3.0
        ---

        # side-effect-entrypoint
        """,
    )

    with pytest.raises(RuntimeError, match="side-effect procedure blocked"):
        PlaybookRuntime(tmp_path).run(
            intent="side_effect_entrypoint",
            question="hello",
            write_side_effects=False,
        )
