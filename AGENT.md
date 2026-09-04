# AGENT.md — Governance + Operating Rules (New-knowledge base MVP)

This repo is a **Markdown-first, execution-oriented knowledge system** inspired by OpenClaw's
skill architecture (SKILL.md + strict frontmatter validation + progressive disclosure).

## Core runtime model
- Runtime is **orchestration**, not retrieval:
  - pick an entrypoint (intent) → execute steps → produce outputs.
- **MVP (pre-v0.3) position**: no vector DB, no BM25 candidate narrowing.
- **v0.3+ position (current, see README "Why This Is Not Just RAG" + docs/RETRIEVAL.md)**:
  retrieval is a deterministic **evidence supply** layer (keyword / BM25 / semantic-lite / hybrid
  via `evolvekb.retrieval`), not the source of agent behavior. Playbooks still decide how
  evidence becomes behavior. The retrieval layer is intentionally credential-free and local;
  it is not a semantic-search superiority claim.

## Progressive disclosure (borrowed pattern)
1) **Metadata** (SKILL.md frontmatter): always-load, small, used for routing + gating.
2) **Body** (SKILL.md markdown): loaded/executed only after the skill triggers.
3) **Bundled resources** (scripts/references/assets): loaded on demand.

## Validation gates (CI)
### Gate 1 — Skill structure
- Every skill must have `SKILL.md` with YAML frontmatter.
- Allowed frontmatter keys are restricted (fail fast).
- Skill name must be hyphen-case (`^[a-z0-9-]+$`), <= 64 chars.

### Gate 2 — Orchestration integrity
- Playbook-skills must declare steps that reference existing procedure-skills.
- No repeated step in a playbook (MVP cycle-like guard).
- Optional: max size limits for SKILL.md files (to keep prompt surface lean).

### Gate 3 — Leanness
- Soft limits:
  - total number of skills loaded is bounded (configurable).
  - SKILL.md size bounded (configurable).

## Evolution protocol
- After a meaningful milestone, create a patch that **replaces** or refactors an existing skill
  rather than appending parallel variants.
- Major refactors should preserve the module contract (or update all callers).
