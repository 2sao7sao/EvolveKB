# Changelog

All notable changes to EvolveKB are documented here.

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

### Changed

- Package version, runtime `__version__`, and default `SkillAsset.version` now align on `0.3.0`.
- Demo capability coverage now comes from a named checklist instead of unnamed
  boolean buckets.
- CLI query and retrieval evals can select a retriever mode.

### Prototype Boundaries

- Keyword retrieval remains a deterministic baseline, not a semantic retrieval claim.
- Current evals are seed-level checks for the product path, not broad benchmark coverage.
