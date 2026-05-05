<img src="assets/banner.png" alt="banner" width="100%" />

# EvolveKB — Your Execution‑First Knowledge Companion

[![Status](https://img.shields.io/badge/status-Concept%20%2F%20WIP-yellow)](./README.md)
[![Stars](https://img.shields.io/github/stars/2sao7sao/EvolveKB?style=flat)](https://github.com/2sao7sao/EvolveKB)
[![Commit Activity](https://img.shields.io/github/commit-activity/m/2sao7sao/EvolveKB)](https://github.com/2sao7sao/EvolveKB/commits/main)
[![License](https://img.shields.io/badge/license-MIT-blue)](./LICENSE)

**Language:** English | [简体中文](README.zh.md)

> Turn knowledge into **executable skills**.  
> Not just storing docs—EvolveKB learns **your knowledge logic**, and evolves it under gates.

---

## Quick links

- [Vision](#vision)
- [Use cases](#use-cases)
- [Knowledge vs Usage](#knowledge-vs-usage)
- [How it works](#how-it-works)
- [Minimal runnable demo](#minimal-runnable-demo)
- [Ingest to knowledge](#ingest-to-knowledge)
- [Mode presets](#mode-presets)
- [Phase 2 updates](#phase-2-updates)
- [Phase 3 updates](#phase-3-updates)
- [Self-iteration loop](#self-iteration-loop)
- [Usage review](#usage-review-weekly)
- [Roadmap](#roadmap)

---

## TL;DR

- A “knowledge sidecar” that focuses on **knowledge logic**, not storage.
- Four modes: **reference / digest / transform / evolve**.
- AI learns what to store, how to use it, and when to update.
- Phase 2 adds a package runtime, typed asset registry, KB index/log, and lintable self-iteration loop.

---

## Vision

**Execution‑first**: make knowledge executable before optimizing retrieval.  
We want AI not only to find facts, but to **organize and apply knowledge** in your preferred logic.

Current status: **Concept / WIP**.

---

## Why

Traditional RAG is good at “finding”, but weak at “turning knowledge into reusable flows”:

- **Shallow understanding**: fragment stitching instead of structured synthesis.
- **Multi‑hop breaks**: chunk boundaries lose cross‑context logic.
- **One‑size usage**: no configurable knowledge strategy per user or task.

---

## What

**EvolveKB = knowledge upgraded into skills**:

- **Playbook**: intent‑level workflow
- **Procedure**: reusable atomic step
- **Settings**: control how knowledge participates in reasoning
- **Gate**: quality control and evolution constraints
- **Index / Log**: navigation and evolution memory for self-iteration

---

## Knowledge vs Usage

EvolveKB separates assets into two types:

- **Knowledge**: distilled, model‑understood information (what we know)
- **Usage**: how to apply knowledge (how we use it)

Directory layout:

```text
evolvekb/       # package runtime, asset registry, gates, CLI
kb/
  index.md     # repo-wide content index
  log.md       # append-only evolution log
  knowledge/   # distilled knowledge blocks
  usage/       # playbooks / procedures / strategies
skills/        # executable SKILL.md playbooks/procedures
settings/      # mode presets and gate settings
scripts/       # legacy wrappers around the package runtime
```

Schema & gate rules: [kb/SCHEMA.md](kb/SCHEMA.md)

## Use cases

- **Beyond vector‑only storage**: knowledge becomes executable, not just retrievable.
- **Continuous evolution**: gated updates with versionable proposals.
- **Personal knowledge logic**: learn how you want to store and use knowledge.

---

## How it works

1. User question / docs input
2. Load settings (reference / digest / transform / evolve)
3. Route to playbook by intent
4. Execute procedures step‑by‑step
5. Gate checks verify intermediate outputs
6. Evolve mode writes a proposal snapshot

---

## Architecture

<img src="assets/architecture.svg" alt="architecture" width="100%" />

---

## Minimal runnable demo

This repo includes a minimal end‑to‑end path (no external tools):

```bash
python -m pip install -r requirements.txt
python scripts/run.py --intent compare_frameworks --question "Compare GraphRAG vs Execution-first" --settings settings/reference.yaml
```

Expected outputs: [examples/demo.md](examples/demo.md) (reference / digest / transform / evolve)

Package CLI:

```bash
python -m pip install -e ".[dev]"
evolvekb validate --settings settings/evolve.yaml
evolvekb run --intent compare_frameworks --question "Compare GraphRAG vs Execution-first" --settings settings/reference.yaml
evolvekb skills list
evolvekb kb index
evolvekb kb lint --gate-level 2
evolvekb query "execution-first knowledge runtime"
evolvekb eval run "evals/*.yaml"
```

Legacy scripts are still supported:

```bash
python scripts/validate.py --settings settings/evolve.yaml
python scripts/run.py --intent compare_frameworks --question "Compare GraphRAG vs Execution-first" --settings settings/reference.yaml
python scripts/ingest.py --doc path/to/your.md
python scripts/review_usage.py
```

---

## Phase 2 updates

Phase 2 turns the original deterministic demo into a package-quality runtime while keeping the minimal scripts compatible.

Implemented:

- **Python package runtime**: `evolvekb/` now contains config loading, asset parsing, registry logic, gate validation, skill routing, playbook execution, ingestion helpers, usage review, and packaging helpers.
- **Installable CLI**: `pyproject.toml` adds the `evolvekb` command and `.[dev]` dependencies.
- **Pydantic schema v2**: core models now cover source documents, chunks, claims, concepts, knowledge blocks, usage assets, skill assets, gate policies, proposals, and run traces.
- **AssetRegistry**: loads knowledge, usage, and skill assets; computes stable hashes; resolves references; catches duplicate IDs, missing skills, unknown knowledge references, and invalid `TBD` usage at stricter gate levels.
- **Skill runtime**: playbooks are selected by intent, procedures are executed step by step, and the old deterministic demo behavior is preserved.
- **Schema migration**: existing `kb/knowledge`, `kb/usage`, and `skills/*/SKILL.md` assets were migrated to `schema_version: 2`.
- **Knowledge/usage seed assets**: `execution-first-kb` was added and `compare-frameworks` now references concrete knowledge assets instead of `uses: TBD`.
- **Settings expansion**: presets now include retrieval flags, proposal review settings, and gate thresholds for later milestones.
- **CI and tests**: GitHub Actions installs the package, validates assets, runs legacy validation smoke, and executes pytest. The current suite covers config, frontmatter, models, registry, gates, skills, runtime, CLI, and legacy wrappers.

New CLI surface:

```bash
evolvekb validate --settings settings/evolve.yaml
evolvekb run --intent compare_frameworks --question "Compare GraphRAG vs Execution-first" --settings settings/reference.yaml
evolvekb skills list
evolvekb skills inspect compare-frameworks
evolvekb kb index
evolvekb kb lint --gate-level 2
evolvekb kb log note "Reviewed a knowledge update"
```

---

## Phase 3 updates

The next roadmap items are now implemented as a minimal local-first loop:

- **Complete gate evolution loop**: `evolvekb evolve doc <path>` compiles a source into a proposal, runs gates, can run evals, and records the action in `kb/log.md`.
- **Claim/evidence ingestion compiler**: `evolvekb ingest <doc>` now writes `kb/sources`, `kb/chunks`, `kb/claims`, `kb/concepts`, and a v2 knowledge asset. `--proposal` creates a reviewable proposal instead of writing canonical knowledge directly.
- **Proposal apply / rollback workflow**: `evolvekb proposal create|list|apply|rollback` supports reviewable write-file proposals, backups, manifests, status updates, rollback, index rebuilds, and log entries.
- **Eval harness**: `evolvekb eval run "evals/*.yaml"` runs YAML eval cases. Current categories cover retrieval and routing.
- **Retrieval-as-evidence**: `evolvekb query <query>` runs keyword retrieval over knowledge blocks and compiled claims, returning an evidence pack with citations.
- **More playbooks and examples**: `answer-with-evidence` adds an evidence-first playbook using `retrieve-evidence` and `compose-evidence-answer`; examples and eval cases were added under `examples/` and `evals/`.

New self-iteration commands:

```bash
evolvekb ingest README.md
evolvekb ingest README.md --proposal
evolvekb query "execution-first knowledge runtime"
evolvekb run --intent answer_with_evidence --question "What is execution-first knowledge?"
evolvekb evolve doc README.md --settings settings/evolve.yaml --eval "evals/*.yaml"
evolvekb proposal list
evolvekb proposal apply <proposal-id-or-path>
evolvekb proposal rollback <proposal-id>
evolvekb eval run "evals/*.yaml"
```

Remaining future work:

- HTTP API
- richer LLM-based claim extraction
- contradiction detection
- semantic/vector and graph retrieval
- human review UI for proposals
- larger eval corpus and more domain playbooks

Phase 2 established the runtime, schema, registry, and self-iteration foundation. Phase 3 turns that foundation into a working local evolution loop.

## Self-iteration loop

EvolveKB borrows from the LLM Wiki pattern: raw sources should stay stable, compiled markdown should accumulate model-understood synthesis, and index/log files should help the model navigate what changed.

EvolveKB specializes this into an execution-first runtime:

- `kb/knowledge/` stores what is known.
- `kb/usage/` stores how knowledge should be applied.
- `skills/` stores executable playbooks and procedures.
- `kb/index.md` is the content-oriented navigation layer.
- `kb/log.md` is the append-only evolution timeline.
- Gates and proposals keep future self-updates reviewable instead of silent.

Reference notes: [Karpathy LLM Wiki comparison](docs/karpathy-llm-wiki-comparison.md)

### Difference from RAG

Traditional RAG retrieves chunks at query time and asks the model to re-synthesize from fragments. EvolveKB's direction is different:

```text
raw sources
  -> model-understood knowledge
  -> explicit usage rules
  -> executable skills
  -> gates / logs / proposals
  -> updated knowledge and usage
```

Retrieval can still be useful later as evidence supply, but it is not the core product. The core product is a self-updating knowledge runtime that records what the model has understood and how that understanding should be used.

### Karpathy LLM Wiki reference

Karpathy's LLM Wiki pattern argues for a persistent markdown wiki maintained by an LLM: immutable raw sources, an LLM-written wiki, a schema file, `index.md`, `log.md`, and periodic linting.

EvolveKB adopts the useful parts:

- keep compiled markdown as a persistent artifact
- maintain a content index for navigation
- maintain a chronological log for evolution memory
- lint the knowledge base for broken references and orphan assets
- let useful queries become candidate updates

EvolveKB differs by adding stricter runtime boundaries:

- `knowledge` and `usage` are separate assets
- `skills` are executable playbooks/procedures
- gates validate structure and references
- future evolution should happen through proposals instead of silent writes
- the system is designed for agent runtime behavior, not only human wiki browsing

---

## Ingest to knowledge

Generate a knowledge asset directly from a markdown file:

Usage evolves separately based on verification and user behavior, and is stored under `kb/usage`.

Auto-usage is generated after playbook runs and reviewed weekly.

```bash
python scripts/ingest.py --doc path/to/your.md
# -> kb/knowledge/<doc_name>.md
```

You can also run the playbook directly:

```bash
python scripts/run.py --intent ingest_doc --doc path/to/your.md --settings settings/transform.yaml
```

## Mode presets

Switch behavior via presets. Output verbosity is controlled by `output_template` in each preset:

```bash
python scripts/run.py --intent compare_frameworks --question "..." --settings settings/reference.yaml
python scripts/run.py --intent compare_frameworks --question "..." --settings settings/digest.yaml
python scripts/run.py --intent compare_frameworks --question "..." --settings settings/transform.yaml
python scripts/run.py --intent compare_frameworks --question "..." --settings settings/evolve.yaml
```

---

## Mode comparison

<img src="assets/mode_matrix.svg" alt="mode comparison" width="100%" />

## Knowledge usage modes

| Mode | Purpose | Typical usage |
| --- | --- | --- |
| Reference | Cite sources, avoid rewriting | Quick Q&A / conservative |
| Digest | Summarize into structured notes | Absorb & summarize |
| Transform | Compile into procedures/playbooks | Build reusable skills |
| Evolve | Propose gated, versioned updates | Continuous evolution |

---

## Versioned proposals

In `evolve` mode, a proposal snapshot is written for review:

```bash
python scripts/run.py --intent compare_frameworks --question "..." --settings settings/evolve.yaml
# -> outputs/proposals/<timestamp>_compare_frameworks.md
```

---

## Gate validation

Run repo validation with a settings file to apply gate rules:

```bash
python scripts/validate.py --settings settings/evolve.yaml
evolvekb validate --settings settings/evolve.yaml
evolvekb kb lint --gate-level 2
```

## Usage review (weekly)

Generate a weekly recap of usage assets and TBD patterns:

```bash
python scripts/review_usage.py
# -> outputs/reviews/usage_review_<timestamp>.md
```

The usage index is auto‑maintained at `kb/usage/index.md`. Usage events are stored in `outputs/usage/events.log`.

## Roadmap

1. ✅ README / product narrative
2. ✅ Settings presets and modes
3. ✅ Minimal runnable demo
4. ✅ Package runtime + CLI
5. ✅ Schema v2 + AssetRegistry
6. ✅ KB index/log + lintable self-iteration loop
7. ✅ Complete gate evolution loop
8. ✅ Claim/evidence ingestion compiler
9. ✅ Proposal apply / rollback workflow
10. ✅ Eval harness and retrieval-as-evidence
11. ✅ More playbooks and examples
12. ⏭️ HTTP API and review UI
13. ⏭️ LLM-backed claim extraction and contradiction checks
14. ⏭️ Hybrid retrieval: keyword + semantic + graph
15. ⏭️ Larger eval corpus and domain playbook library

---

## Validation

Current validation target:

```bash
python -m pip install -e ".[dev]"
pytest -q
ruff check evolvekb tests scripts
python -m evolvekb.cli validate --settings settings/evolve.yaml
python scripts/validate.py --settings settings/evolve.yaml
python -m evolvekb.cli kb lint --gate-level 2
python -m evolvekb.cli eval run "evals/*.yaml"
```

---

## Star history

![Star History](https://api.star-history.com/svg?repos=2sao7sao/EvolveKB&type=Date)

---

## Commit activity

![Commit Activity Graph](https://github-readme-activity-graph.vercel.app/graph?username=2sao7sao&repo=EvolveKB&theme=github-compact)

---

## License

See `LICENSE`.
