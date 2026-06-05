# Proposal Review

EvolveKB proposals describe knowledge behavior changes, not just file writes.
New proposals include impact metadata so reviewers can inspect affected assets,
rollback paths, safety signals, and related evals.

## Impact Metadata

```yaml
impact:
  changed_claims:
    added:
      - claim_src_demo_0001
    modified: []
    superseded: []
    rejected: []
  impacted_knowledge_ids:
    - refund-policy
  impacted_usage_ids: []
  impacted_skill_ids: []
  impacted_eval_ids: []
  conflicts_detected: []
  rollback_plan:
    files:
      - kb/knowledge/refund-policy.md
    before_hashes:
      kb/knowledge/refund-policy.md: ""
    restore_from: kb/proposals/applied/
  safety_assessment:
    private_data: false
    prompt_injection_risk: low
    requires_human_review: true
```

## Gates

| Gate | Behavior |
| --- | --- |
| `proposal_has_impact_summary` | Blocks proposals without impact metadata or impacted assets. |
| `proposal_has_rollback_plan` | Blocks proposals without rollback files and pre-change hashes. |
| `claim_has_evidence_quote` | Blocks active claims missing an evidence quote. |
| `proposal_impacted_evals_declared` | Emits a v0.3 warning when no impacted evals are declared. |

## Reviewer Checklist

- The proposal has a clear rationale.
- Impact metadata names the changed assets.
- Rollback plan includes files and before hashes.
- Safety assessment does not hide private data or prompt-injection risk.
- Related evals are listed when the impacted behavior has known regression seeds.
