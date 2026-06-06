from __future__ import annotations

import json
from pathlib import Path

from evolvekb.assets.frontmatter import parse_frontmatter
from evolvekb.evolution.proposal import create_write_file_proposal
from evolvekb.gates.engine import validate_claim_evidence, validate_proposal_metadata


def test_create_write_file_proposal_includes_impact_metadata(tmp_path: Path) -> None:
    proposal = create_write_file_proposal(
        repo=tmp_path,
        title="Create refund policy",
        proposal_type="knowledge_update",
        path="kb/knowledge/refund-policy.md",
        content="# Refund Policy\n",
        rationale="Add reviewed refund policy.",
        evidence_ids=["claim_refund_001"],
    )

    fm = parse_frontmatter(proposal.read_text(encoding="utf-8")).frontmatter
    impact = fm["impact"]
    assert impact["changed_claims"]["added"] == ["claim_refund_001"]
    assert impact["impacted_knowledge_ids"] == ["refund-policy"]
    assert impact["rollback_plan"]["files"] == ["kb/knowledge/refund-policy.md"]
    assert "before_hashes" in impact["rollback_plan"]
    assert impact["safety_assessment"]["requires_human_review"] is True
    assert [item for item in validate_proposal_metadata(tmp_path) if not item.passed] == []


def test_proposal_metadata_gate_blocks_missing_impact(tmp_path: Path) -> None:
    proposal_dir = tmp_path / "kb" / "proposals"
    proposal_dir.mkdir(parents=True)
    (proposal_dir / "bad.md").write_text(
        """---
schema_version: 2
id: prop_bad
title: Bad proposal
proposal_type: knowledge_update
status: pending_review
impacted_assets:
  - kb/knowledge/demo.md
before_hashes: {}
after_patches: []
evidence_ids: []
eval_results: {}
created_at: 2026-06-05T00:00:00Z
---

# Bad proposal
""",
        encoding="utf-8",
    )

    failures = [item for item in validate_proposal_metadata(tmp_path) if not item.passed]
    assert any(item.gate_id == "proposal_has_impact_summary" for item in failures)
    assert any(item.gate_id == "proposal_has_rollback_plan" for item in failures)


def test_claim_evidence_gate_blocks_active_claim_without_quote(tmp_path: Path) -> None:
    claims_dir = tmp_path / "kb" / "claims"
    claims_dir.mkdir(parents=True)
    (claims_dir / "claims.jsonl").write_text(
        json.dumps(
            {
                "id": "claim_missing_quote",
                "status": "active",
                "text": "A claim without evidence.",
                "evidence_quote": "",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    failures = [item for item in validate_claim_evidence(tmp_path) if not item.passed]
    assert failures
    assert failures[0].gate_id == "claim_has_evidence_quote"
