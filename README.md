<img src="assets/banner.png" alt="banner" width="100%" />

# EvolveKB

[![Status](https://img.shields.io/badge/status-Concept%20%2F%20WIP-yellow)](./README.md)
[![Stars](https://img.shields.io/github/stars/2sao7sao/EvolveKB?style=flat)](https://github.com/2sao7sao/EvolveKB)
[![Commit Activity](https://img.shields.io/github/commit-activity/m/2sao7sao/EvolveKB)](https://github.com/2sao7sao/EvolveKB/commits/main)
[![License](https://img.shields.io/badge/license-MIT-blue)](./LICENSE)

**Language:** English | [简体中文](README.zh.md)

EvolveKB is an execution-first knowledge runtime. It turns source material into structured knowledge, records how that knowledge should be used, routes tasks into executable skills, and evolves the knowledge base through gates, proposals, logs, and evals.

The goal is not to build another vector-store wrapper. EvolveKB treats knowledge as something the model can understand, record, validate, use, and update.

## Contents

- [Why EvolveKB](#why-evolvekb)
- [Current Status](#current-status)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [How It Works](#how-it-works)
- [CLI Reference](#cli-reference)
- [Project Layout](#project-layout)
- [Self-Iteration Model](#self-iteration-model)
- [Examples](#examples)
- [Development](#development)
- [Roadmap](#roadmap)

## Why EvolveKB

Traditional RAG retrieves chunks at query time and asks the model to synthesize an answer from fragments. That is useful, but it does not preserve how knowledge should be applied.

EvolveKB takes a different path:

```text
source material
  -> claims, concepts, knowledge blocks
  -> usage rules
  -> executable skills
  -> gates, evals, proposals, logs
  -> reviewed knowledge updates
```

Retrieval still exists, but only as evidence supply. The main artifact is a knowledge base that can improve itself under review.

## Current Status

EvolveKB is a local-first concept/WIP with a working Python runtime and CLI.

What works today:

- Installable `evolvekb` package and CLI.
- `schema_version: 2` assets for knowledge, usage, skills, gates, proposals, and traces.
- Asset registry with reference validation and stable hashing.
- Playbook runtime for deterministic skill execution.
- Markdown ingestion into sources, chunks, claims, concepts, and knowledge assets.
- Keyword retrieval over knowledge blocks and compiled claims.
- Proposal creation, application, rollback, backup manifests, index rebuilds, and logs.
- YAML eval runner for retrieval and routing checks.
- KB index, KB log, and lint commands for self-iteration hygiene.
- Legacy `scripts/*.py` wrappers for existing commands.

Still planned:

- HTTP API and review UI.
- LLM-backed claim extraction.
- Contradiction detection.
- Semantic/vector and graph retrieval.
- Larger eval corpus and domain playbook library.

## Quick Start

```bash
python -m pip install -e ".[dev]"
evolvekb validate --settings settings/evolve.yaml
```

Run the original comparison demo:

```bash
evolvekb run \
  --intent compare_frameworks \
  --question "Compare GraphRAG vs Execution-first" \
  --settings settings/reference.yaml
```

Run an evidence-backed answer:

```bash
evolvekb run \
  --intent answer_with_evidence \
  --question "What is execution-first knowledge?"
```

Ingest a Markdown document into the KB:

```bash
evolvekb ingest README.md
```

Create an ingest proposal instead of writing canonical knowledge directly:

```bash
evolvekb ingest README.md --proposal
```

Run evals:

```bash
evolvekb eval run "evals/*.yaml"
```

Legacy commands still work:

```bash
python scripts/validate.py --settings settings/evolve.yaml
python scripts/run.py --intent compare_frameworks --question "Compare GraphRAG vs Execution-first"
python scripts/ingest.py --doc README.md
python scripts/review_usage.py
```

## Core Concepts

| Concept | Meaning |
| --- | --- |
| Knowledge | What the system knows. Stored as structured knowledge blocks under `kb/knowledge/`. |
| Usage | How knowledge should be applied. Stored under `kb/usage/`. |
| Skill | Executable playbooks and procedures in `skills/*/SKILL.md`. |
| Playbook | Intent-level workflow that calls one or more procedures. |
| Procedure | Reusable atomic step in a playbook. |
| Gate | Validation rule that blocks or flags unsafe/invalid assets or updates. |
| Proposal | Reviewable change transaction before mutating canonical KB assets. |
| Eval | Regression case for routing, retrieval, gates, outputs, or evolution. |
| Index | `kb/index.md`, a navigable map of knowledge, usage, and skills. |
| Log | `kb/log.md`, an append-only record of evolution events. |

## How It Works

```text
User query / source document
  -> settings and intent routing
  -> optional evidence retrieval
  -> playbook runtime
  -> gate validation
  -> answer, proposal, or KB update
  -> index/log/eval feedback
```

For document ingestion:

```text
Markdown document
  -> SourceDocument
  -> SourceChunk
  -> Claim
  -> Concept
  -> KnowledgeBlock
  -> proposal or canonical write
```

For self-iteration:

```text
run / ingest / query result
  -> lint and gates
  -> evals
  -> proposal
  -> apply or rollback
  -> index rebuild
  -> log entry
```

## CLI Reference

Validation:

```bash
evolvekb validate --settings settings/evolve.yaml
evolvekb kb lint --gate-level 2
```

Knowledge and retrieval:

```bash
evolvekb ingest README.md
evolvekb ingest README.md --proposal
evolvekb query "execution-first knowledge runtime"
```

Playbooks and skills:

```bash
evolvekb run --intent compare_frameworks --question "Compare GraphRAG vs Execution-first"
evolvekb run --intent answer_with_evidence --question "What is execution-first knowledge?"
evolvekb skills list
evolvekb skills inspect compare-frameworks
```

Evolution workflow:

```bash
evolvekb evolve doc README.md --settings settings/evolve.yaml --eval "evals/*.yaml"
evolvekb proposal list
evolvekb proposal apply <proposal-id-or-path>
evolvekb proposal rollback <proposal-id>
```

Index, log, and evals:

```bash
evolvekb kb index
evolvekb kb log note "Reviewed a knowledge update"
evolvekb eval run "evals/*.yaml"
```

## Project Layout

```text
evolvekb/
  assets/       # frontmatter, loading, registry, hashing
  core/         # pydantic models and settings
  evals/        # YAML eval runner
  evolution/    # proposal create/apply/rollback
  gates/        # validation gates
  ingestion/    # deterministic markdown compiler
  retrieval/    # keyword retrieval as evidence supply
  skills/       # skill registry and playbook runtime
kb/
  index.md      # generated KB map
  log.md        # append-only evolution log
  knowledge/    # canonical knowledge assets
  usage/        # canonical usage assets
skills/         # SKILL.md playbooks and procedures
settings/       # mode presets
evals/          # eval cases
examples/       # runnable examples and expected outputs
scripts/        # legacy wrappers
tests/          # pytest suite
```

Schema details live in [kb/SCHEMA.md](kb/SCHEMA.md).

## Self-Iteration Model

EvolveKB is influenced by Karpathy's LLM Wiki pattern: keep raw sources stable, maintain model-written markdown, use an index and log, and lint the wiki regularly.

EvolveKB adapts that idea into a runtime:

- Knowledge and usage are separate assets.
- Skills are executable and routed by intent.
- Retrieval supplies evidence, but does not define the whole system.
- Proposals are reviewable transactions, not silent writes.
- Gates and evals decide whether updates are safe enough to apply.

Reference notes: [Karpathy LLM Wiki comparison](docs/karpathy-llm-wiki-comparison.md)

## Examples

Comparison playbook:

```bash
evolvekb run \
  --intent compare_frameworks \
  --question "Compare GraphRAG vs Execution-first"
```

Evidence-backed answer:

```bash
evolvekb run \
  --intent answer_with_evidence \
  --question "What is execution-first knowledge?"
```

Eval smoke suite:

```bash
evolvekb eval run "evals/*.yaml"
```

See:

- [examples/demo.md](examples/demo.md)
- [examples/evidence_answer.md](examples/evidence_answer.md)

## Development

Install development dependencies:

```bash
python -m pip install -e ".[dev]"
```

Run checks:

```bash
pytest -q
ruff check evolvekb tests scripts
python -m evolvekb.cli validate --settings settings/evolve.yaml
python scripts/validate.py --settings settings/evolve.yaml
python -m evolvekb.cli eval run "evals/*.yaml"
```

The current test suite covers settings, frontmatter parsing, Pydantic models, asset registry, gates, skill routing, runtime execution, ingestion, retrieval, proposals, evals, CLI commands, and legacy wrappers.

## Roadmap

Done:

- README and product framing.
- Settings presets and mode-aware output.
- Minimal end-to-end demo.
- Package runtime and CLI.
- Schema v2 and AssetRegistry.
- KB index/log and lintable self-iteration loop.
- Gate evolution loop.
- Claim/evidence ingestion compiler.
- Proposal apply/rollback workflow.
- Eval harness and retrieval-as-evidence.
- Additional playbook: `answer-with-evidence`.

Next:

- HTTP API and proposal review UI.
- LLM-backed claim extraction.
- Contradiction and supersession checks.
- Hybrid retrieval: keyword + semantic + graph.
- Larger eval corpus.
- More domain playbooks and examples.

## License

See [LICENSE](LICENSE).
