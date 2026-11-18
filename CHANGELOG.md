# Changelog

All notable changes to EvolveKB are documented here.

## 0.4.0 - 2026-11-18

First tagged release. `0.3.0` was a source-package version; no tag or GitHub
Release existed before this one.

### Added

- Pluggable retriever registry: named adapters can be registered and selected
  from settings, with contrib TF-IDF (`evolvekb/retrieval/contrib/tfidf.py`) and
  regex (`evolvekb/retrieval/contrib/regex.py`) retrievers alongside keyword,
  BM25, hybrid, and semantic-lite.
- `docs/maintenance.md` records the 2026-11-16 maintenance review, the checks it
  ran, and their evidence boundaries.
- Validate reports include gate counts and the conflicts field; `docs/RUNTIME_TRACE.md`
  documents `StepTrace.gate_results`.

### Changed

- Package version, runtime `__version__`, and default `SkillAsset.version` align
  on `0.4.0`.
- README, brand assets, and issue templates refreshed in both languages; `AGENT.md`
  aligned with the current retrieval position.
- Pages deployment workflow is manual-only until the repository has Pages enabled.

### Prototype Boundaries

- Keyword, TF-IDF, and regex retrieval are deterministic baselines, not semantic
  retrieval claims.
- Evals are seed-level checks for the product path, not production benchmark
  coverage; this release makes no production-quality claim.

## 0.3.0 - 2026-06-05

### Added

- First-screen README positioning for EvolveKB as an execution-first knowledge runtime.
- Real CI, Python, version, and license badges in the English and Chinese READMEs.
- Metric documentation for the flagship demo, including the seed-level
  `retrieval_vs_playbook_delta` formula and capability checklist.
- Contributor onboarding with first-PR ideas, local checks, skill contribution
  guidance, eval case guidance, and security rules.
- Annotated `SKILL.md` template for new playbooks and procedures.
- Issue templates for skill contributions and eval cases.
- Demo asset provenance notes for the README terminal image.
- `EvidencePack` contract with keyword, BM25, hybrid, and semantic retriever registry hooks.
- `docs/RETRIEVAL.md` with retriever modes, CLI examples, settings, and eval mode selection.
- Step-level `RunTrace` with CLI `--trace` and `--trace-out` support.
- Python procedure executor support for `metadata.runtime.entrypoint`.
- Customer support refund agent example with refund decision playbook.
- Eval matrix categories for claim extraction, grounding, playbook execution, baseline comparison, and evolution safety.
- Proposal impact metadata, rollback plan, safety assessment, and proposal/claim gates.
- Deterministic semantic-lite retriever and hybrid semantic score merge.

### Changed

- Package version, runtime `__version__`, and default `SkillAsset.version` now align on `0.3.0`.
- Demo capability coverage now comes from a named checklist instead of unnamed
  boolean buckets.
- CLI query and retrieval evals can select a retriever mode.

### Prototype Boundaries

- Keyword retrieval remains a deterministic baseline, not a semantic retrieval claim.
- Current evals are seed-level checks for the product path, not broad benchmark coverage.
