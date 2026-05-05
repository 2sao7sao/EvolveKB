from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest
from pydantic import ValidationError

from evolvekb.assets.frontmatter import dump_frontmatter, parse_frontmatter
from evolvekb.assets.registry import AssetRegistry
from evolvekb.core.config import Settings, load_settings
from evolvekb.core.models import (
    Claim,
    GatePolicy,
    KnowledgeBlock,
    Proposal,
    RunTrace,
    SkillAsset,
    UsageAsset,
)
from evolvekb.gates.engine import validate_repo
from evolvekb.skills.registry import SkillRegistry
from evolvekb.skills.runtime import PlaybookRuntime, compose_knowledge_from_doc
from evolvekb.wiki import append_kb_log, lint_kb, rebuild_kb_index


REPO = Path(__file__).resolve().parents[1]


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text).lstrip(), encoding="utf-8")


def run_cmd(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=REPO, text=True, capture_output=True, check=False)


def test_settings_defaults() -> None:
    settings = Settings()
    assert settings.knowledge_mode == "reference"
    assert settings.gate_level == 1


def test_settings_load_relative_file() -> None:
    settings = load_settings(REPO, "settings/reference.yaml")
    assert settings.knowledge_mode == "reference"
    assert settings.output_template == "compact"


def test_settings_reject_invalid_mode(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text("knowledge_mode: nope\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_settings(tmp_path, path)


def test_settings_reject_invalid_template(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text("output_template: huge\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_settings(tmp_path, path)


def test_settings_reject_invalid_gate_level(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text("gate_level: 9\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_settings(tmp_path, path)


def test_settings_coerces_gate_level() -> None:
    assert Settings(gate_level="2").gate_level == 2


def test_frontmatter_parse_valid() -> None:
    doc = parse_frontmatter("---\nname: demo\n---\n# Body\n")
    assert doc.frontmatter["name"] == "demo"


def test_frontmatter_rejects_missing_header() -> None:
    with pytest.raises(ValueError):
        parse_frontmatter("# Body\n")


def test_frontmatter_rejects_non_mapping() -> None:
    with pytest.raises(ValueError):
        parse_frontmatter("---\n- nope\n---\nBody\n")


def test_frontmatter_preserves_body() -> None:
    doc = parse_frontmatter("---\nname: demo\n---\nLine 1\nLine 2\n")
    assert doc.body == "Line 1\nLine 2\n"


def test_dump_frontmatter_roundtrip() -> None:
    rendered = dump_frontmatter({"name": "demo"}, "\n# Demo\n")
    assert parse_frontmatter(rendered).frontmatter["name"] == "demo"


def test_knowledge_model_valid() -> None:
    asset = KnowledgeBlock(
        id="kb_demo",
        name="demo",
        block_type="reference",
        summary="Demo",
        concepts=[],
        updated_at="2026-05-01",
    )
    assert asset.kind == "knowledge"


def test_knowledge_model_rejects_invalid_block_type() -> None:
    with pytest.raises(ValidationError):
        KnowledgeBlock(
            id="kb_demo",
            name="demo",
            block_type="bad",
            summary="Demo",
            updated_at="2026-05-01",
        )


def test_usage_model_valid() -> None:
    asset = UsageAsset(
        id="usage_demo",
        name="demo",
        intent="demo",
        strategy="playbook",
        pattern="required",
        uses=["demo-kb"],
        updated_at="2026-05-01",
    )
    assert asset.strategy == "playbook"


def test_usage_model_rejects_invalid_pattern() -> None:
    with pytest.raises(ValidationError):
        UsageAsset(
            id="usage_demo",
            name="demo",
            intent="demo",
            strategy="playbook",
            pattern="sometimes",
            updated_at="2026-05-01",
        )


def test_skill_model_valid() -> None:
    skill = SkillAsset(name="demo", description="A demo skill", kind="procedure")
    assert skill.version == "0.2.0"


def test_skill_model_rejects_invalid_kind() -> None:
    with pytest.raises(ValidationError):
        SkillAsset(name="demo", description="A demo skill", kind="other")


def test_gate_policy_model_valid() -> None:
    gate = GatePolicy(
        id="gate_demo",
        name="demo",
        scope="output",
        level=2,
        failure_action="review_required",
        updated_at="2026-05-01",
    )
    assert gate.kind == "gate_policy"


def test_proposal_model_valid() -> None:
    proposal = Proposal(
        id="prop_demo",
        title="Demo",
        proposal_type="knowledge_update",
        status="draft",
        rationale="Demo",
        created_at=datetime.now(timezone.utc),
    )
    assert proposal.impacted_assets == []


def test_run_trace_model_valid() -> None:
    trace = RunTrace(
        id="trace_demo",
        intent="compare_frameworks",
        mode="reference",
        output_hash="abc",
        created_at=datetime.now(timezone.utc),
    )
    assert trace.step_traces == []


def test_claim_rejects_invalid_confidence() -> None:
    with pytest.raises(ValidationError):
        Claim(
            id="claim_demo",
            source_id="src",
            text="Demo",
            claim_type="fact",
            confidence=2,
            evidence_quote="Demo",
        )


def test_registry_loads_current_assets() -> None:
    registry = AssetRegistry.load(REPO)
    assert "graphrag-core" in registry.knowledge
    assert "compare-frameworks" in registry.usage
    assert "compare-frameworks" in registry.skills


def test_registry_generates_hashes() -> None:
    registry = AssetRegistry.load(REPO)
    assert registry.asset_hashes["skill:compare-frameworks"]


def test_registry_resolves_current_usage_refs_at_gate2() -> None:
    failures = AssetRegistry.load(REPO).failed_results(gate_level=2)
    assert failures == []


def test_registry_detects_duplicate_asset_ids(tmp_path: Path) -> None:
    for name in ["a", "b"]:
        write(
            tmp_path / "kb" / "knowledge" / f"{name}.md",
            f"""
            ---
            schema_version: 2
            id: kb_duplicate
            name: {name}
            kind: knowledge
            block_type: reference
            summary: Demo
            concepts: []
            updated_at: 2026-05-01
            ---
            # Demo
            """,
        )
    failures = AssetRegistry.load(tmp_path).failed_results(gate_level=2)
    assert any("duplicate asset id" in failure.message for failure in failures)


def test_registry_detects_unknown_knowledge_ref(tmp_path: Path) -> None:
    write(
        tmp_path / "kb" / "usage" / "demo.md",
        """
        ---
        schema_version: 2
        id: usage_demo
        name: demo
        kind: usage
        intent: demo
        strategy: playbook
        pattern: required
        uses: [missing]
        steps: []
        updated_at: 2026-05-01
        ---
        # Demo
        """,
    )
    failures = AssetRegistry.load(tmp_path).failed_results(gate_level=2)
    assert any("unknown knowledge" in failure.message for failure in failures)


def test_registry_allows_tbd_at_gate1(tmp_path: Path) -> None:
    write(
        tmp_path / "kb" / "usage" / "demo.md",
        """
        ---
        name: demo
        kind: usage
        intent: demo
        strategy: playbook
        pattern: TBD
        uses: [TBD]
        steps: []
        updated_at: 2026-05-01
        ---
        # Demo
        """,
    )
    assert AssetRegistry.load(tmp_path).failed_results(gate_level=1) == []


def test_registry_blocks_tbd_at_gate2(tmp_path: Path) -> None:
    write(
        tmp_path / "kb" / "usage" / "demo.md",
        """
        ---
        name: demo
        kind: usage
        intent: demo
        strategy: playbook
        pattern: TBD
        uses: [TBD]
        steps: []
        updated_at: 2026-05-01
        ---
        # Demo
        """,
    )
    failures = AssetRegistry.load(tmp_path).failed_results(gate_level=2)
    assert any("TBD" in failure.message for failure in failures)


def test_skill_registry_lists_compare_frameworks() -> None:
    names = [skill.name for skill in SkillRegistry.load(REPO).list()]
    assert "compare-frameworks" in names


def test_skill_registry_picks_playbook_by_intent() -> None:
    skill = SkillRegistry.load(REPO).pick_playbook("compare_frameworks")
    assert skill.name == "compare-frameworks"


def test_skill_registry_rejects_unknown_intent() -> None:
    with pytest.raises(KeyError):
        SkillRegistry.load(REPO).pick_playbook("missing")


def test_skill_registry_rejects_unknown_inspect() -> None:
    with pytest.raises(KeyError):
        SkillRegistry.load(REPO).inspect("missing")


def test_registry_detects_unknown_procedure_step(tmp_path: Path) -> None:
    write(
        tmp_path / "skills" / "demo" / "SKILL.md",
        """
        ---
        schema_version: 2
        name: demo
        description: Demo playbook
        metadata:
          kind: playbook
          intent: demo
          steps:
            - call: missing
          version: 0.2.0
        ---
        # Demo
        """,
    )
    failures = AssetRegistry.load(tmp_path).failed_results(gate_level=1)
    assert any("unknown procedure" in failure.message for failure in failures)


def test_runtime_compare_demo_output() -> None:
    result = PlaybookRuntime(REPO).run(
        "compare_frameworks",
        question="Compare GraphRAG vs Execution-first",
        settings_arg="settings/reference.yaml",
        write_side_effects=False,
    )
    assert "GraphRAG" in result.rendered
    assert "Execution-first" in result.rendered


def test_runtime_ingest_doc_outputs_v2_knowledge(tmp_path: Path) -> None:
    doc = tmp_path / "doc.md"
    doc.write_text("# Title\n\nA short summary.\n", encoding="utf-8")
    name, knowledge_md = compose_knowledge_from_doc(str(doc))
    assert name == "doc"
    assert "schema_version: 2" in knowledge_md


def test_validate_repo_has_no_failures() -> None:
    assert [r for r in validate_repo(REPO, "settings/evolve.yaml") if not r.passed] == []


def test_validate_repo_enforces_skill_size(tmp_path: Path) -> None:
    write(
        tmp_path / "settings.yaml",
        """
        gate_level: 1
        max_skill_md_bytes: 10
        """,
    )
    write(
        tmp_path / "skills" / "demo" / "SKILL.md",
        """
        ---
        schema_version: 2
        name: demo
        description: Demo procedure
        metadata:
          kind: procedure
          inputs:
            value: str
          outputs:
            value: str
          version: 0.2.0
        ---
        # Demo
        """,
    )
    failures = [r for r in validate_repo(tmp_path, "settings.yaml") if not r.passed]
    assert any("too large" in failure.message for failure in failures)


def test_cli_validate_module() -> None:
    result = run_cmd(sys.executable, "-m", "evolvekb.cli", "validate", "--settings", "settings/evolve.yaml")
    assert result.returncode == 0
    assert "REPO VALIDATION PASSED" in result.stdout


def test_cli_skills_inspect() -> None:
    result = run_cmd(sys.executable, "-m", "evolvekb.cli", "skills", "inspect", "compare-frameworks")
    assert result.returncode == 0
    assert '"name": "compare-frameworks"' in result.stdout


def test_legacy_validate_wrapper() -> None:
    result = run_cmd(sys.executable, "scripts/validate.py", "--settings", "settings/evolve.yaml")
    assert result.returncode == 0
    assert "REPO VALIDATION PASSED" in result.stdout


def test_legacy_run_wrapper() -> None:
    result = run_cmd(
        sys.executable,
        "scripts/run.py",
        "--intent",
        "compare_frameworks",
        "--question",
        "Compare GraphRAG vs Execution-first",
        "--settings",
        "settings/reference.yaml",
        "--no-side-effects",
    )
    assert result.returncode == 0
    assert "GraphRAG" in result.stdout


def test_legacy_kb_validate_wrapper() -> None:
    result = run_cmd(sys.executable, "scripts/kb_validate.py", "--gate-level", "2")
    assert result.returncode == 0
    assert "KB VALIDATION PASSED" in result.stdout


def test_legacy_skill_validate_wrapper() -> None:
    result = run_cmd(sys.executable, "scripts/skill_validate.py", "--gate-level", "2")
    assert result.returncode == 0
    assert "VALIDATION PASSED" in result.stdout


def test_rebuild_kb_index_writes_navigation_file(tmp_path: Path) -> None:
    write(
        tmp_path / "kb" / "knowledge" / "demo.md",
        """
        ---
        schema_version: 2
        id: kb_demo
        name: demo
        kind: knowledge
        block_type: reference
        summary: Demo knowledge
        concepts: [demo]
        updated_at: 2026-05-01
        ---
        # Demo
        """,
    )
    path = rebuild_kb_index(tmp_path)
    text = path.read_text(encoding="utf-8")
    assert "## Knowledge" in text
    assert "[[knowledge/demo]]" in text


def test_append_kb_log_writes_parseable_entry(tmp_path: Path) -> None:
    path = append_kb_log(tmp_path, "test", "Created entry")
    text = path.read_text(encoding="utf-8")
    assert "## [" in text
    assert "test | Created entry" in text


def test_lint_kb_reports_orphan_knowledge(tmp_path: Path) -> None:
    write(
        tmp_path / "kb" / "knowledge" / "demo.md",
        """
        ---
        schema_version: 2
        id: kb_demo
        name: demo
        kind: knowledge
        block_type: reference
        summary: Demo knowledge
        concepts: [demo]
        updated_at: 2026-05-01
        ---
        # Demo
        """,
    )
    issues = lint_kb(tmp_path, gate_level=1)
    assert any(issue.code == "orphan_knowledge" for issue in issues)


def test_cli_kb_lint_passes_current_repo() -> None:
    result = run_cmd(sys.executable, "-m", "evolvekb.cli", "kb", "lint", "--gate-level", "2")
    assert result.returncode == 0
    assert "KB LINT PASSED" in result.stdout
