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
- [Ingest a document](#ingest-a-document)
- [Mode presets](#mode-presets)
- [Roadmap](#roadmap)

---

## TL;DR

- A “knowledge sidecar” that focuses on **knowledge logic**, not storage.
- Four modes: **reference / digest / transform / evolve**.
- AI learns what to store, how to use it, and when to update.

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

---

## Knowledge vs Usage

EvolveKB separates assets into two types:

- **Knowledge**: distilled, model‑understood information (what we know)
- **Usage**: how to apply knowledge (how we use it)

Directory layout:

```text
kb/
  knowledge/   # distilled knowledge blocks
  usage/       # playbooks / procedures / strategies
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

---

## Ingest a document

Generate a procedure skill draft directly from a markdown file:

```bash
python scripts/ingest.py --doc path/to/your.md
# -> skills/ingest-<doc_name>/SKILL.md
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
```

## Roadmap

1. ✅ README / product narrative
2. ✅ Settings presets and modes
3. ✅ Minimal runnable demo
4. ⏭️ Core skill schema & gate rules
5. ⏭️ Gate evolution loop
6. ⏭️ More playbooks and examples

---

## Star history

![Star History](https://api.star-history.com/svg?repos=2sao7sao/EvolveKB&type=Date)

---

## Commit activity

![Commit Activity Graph](https://github-readme-activity-graph.vercel.app/graph?username=2sao7sao&repo=EvolveKB&theme=github-compact)

---

## License

See `LICENSE`.
