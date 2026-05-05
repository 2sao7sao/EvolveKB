<img src="assets/banner.png" alt="banner" width="100%" />

# EvolveKB

[![状态](https://img.shields.io/badge/status-Concept%20%2F%20WIP-yellow)](./README.md)
[![Stars](https://img.shields.io/github/stars/2sao7sao/EvolveKB?style=flat)](https://github.com/2sao7sao/EvolveKB)
[![Commit Activity](https://img.shields.io/github/commit-activity/m/2sao7sao/EvolveKB)](https://github.com/2sao7sao/EvolveKB/commits/main)
[![License](https://img.shields.io/badge/license-MIT-blue)](./LICENSE)

**语言：** [English](README.md) | 简体中文

EvolveKB 是一个 execution-first knowledge runtime。它把 source material 编译成结构化知识，记录这些知识应该如何被使用，把任务路由到可执行 skills，并通过 gates、proposals、logs 和 evals 让知识库持续演进。

它的目标不是再做一个 vector-store wrapper，而是让模型能够理解、记录、验证、使用和更新知识。

## 目录

- [为什么需要 EvolveKB](#为什么需要-evolvekb)
- [当前状态](#当前状态)
- [快速开始](#快速开始)
- [核心概念](#核心概念)
- [工作机制](#工作机制)
- [CLI 参考](#cli-参考)
- [项目结构](#项目结构)
- [自我迭代模型](#自我迭代模型)
- [示例](#示例)
- [开发](#开发)
- [路线图](#路线图)

## 为什么需要 EvolveKB

传统 RAG 在查询时召回 chunks，再让模型从碎片中临时综合答案。这个路径有价值，但它不会沉淀“知识应该如何被使用”。

EvolveKB 走另一条路径：

```text
source material
  -> claims, concepts, knowledge blocks
  -> usage rules
  -> executable skills
  -> gates, evals, proposals, logs
  -> reviewed knowledge updates
```

Retrieval 仍然存在，但它只是 evidence supply。核心产物是一个可以在审阅和门控下持续改进的知识库。

## 当前状态

EvolveKB 目前是 local-first 的 Concept / WIP，已经具备可运行的 Python runtime 和 CLI。

当前已支持：

- 可安装的 `evolvekb` package 和 CLI。
- `schema_version: 2` 的 knowledge、usage、skills、gates、proposals、traces 资产。
- AssetRegistry，支持引用校验和稳定 hash。
- Playbook runtime，支持 deterministic skill execution。
- Markdown ingestion，输出 sources、chunks、claims、concepts 和 knowledge assets。
- 对 knowledge blocks 和 compiled claims 的 keyword retrieval。
- Proposal create/apply/rollback、backup manifest、index rebuild 和 log。
- YAML eval runner，覆盖 retrieval 和 routing。
- KB index、KB log、lint 命令，用于自我迭代维护。
- 兼容旧 `scripts/*.py` 命令。

后续计划：

- HTTP API 和 review UI。
- LLM-backed claim extraction。
- Contradiction detection。
- Semantic/vector 和 graph retrieval。
- 更大的 eval corpus 和领域 playbook library。

## 快速开始

```bash
python -m pip install -e ".[dev]"
evolvekb validate --settings settings/evolve.yaml
```

运行原始对比 demo：

```bash
evolvekb run \
  --intent compare_frameworks \
  --question "对比 GraphRAG 和 Execution-first" \
  --settings settings/reference.yaml
```

运行证据优先回答：

```bash
evolvekb run \
  --intent answer_with_evidence \
  --question "What is execution-first knowledge?"
```

把 Markdown 文档摄取进 KB：

```bash
evolvekb ingest README.md
```

生成 ingest proposal，而不是直接写 canonical knowledge：

```bash
evolvekb ingest README.md --proposal
```

运行 evals：

```bash
evolvekb eval run "evals/*.yaml"
```

旧命令仍然可用：

```bash
python scripts/validate.py --settings settings/evolve.yaml
python scripts/run.py --intent compare_frameworks --question "对比 GraphRAG 和 Execution-first"
python scripts/ingest.py --doc README.md
python scripts/review_usage.py
```

## 核心概念

| 概念 | 含义 |
| --- | --- |
| Knowledge | 系统知道什么。存放在 `kb/knowledge/`。 |
| Usage | 知识应该如何被使用。存放在 `kb/usage/`。 |
| Skill | `skills/*/SKILL.md` 中的可执行 playbooks 和 procedures。 |
| Playbook | 面向 intent 的工作流，会调用一个或多个 procedures。 |
| Procedure | Playbook 中可复用的原子步骤。 |
| Gate | 用于阻断或标记无效资产、危险更新的校验规则。 |
| Proposal | 修改 canonical KB 前的可审阅变更事务。 |
| Eval | 用于 routing、retrieval、gates、outputs、evolution 的回归用例。 |
| Index | `kb/index.md`，knowledge、usage、skills 的导航图。 |
| Log | `kb/log.md`，追加式演进记录。 |

## 工作机制

```text
User query / source document
  -> settings and intent routing
  -> optional evidence retrieval
  -> playbook runtime
  -> gate validation
  -> answer, proposal, or KB update
  -> index/log/eval feedback
```

文档摄取路径：

```text
Markdown document
  -> SourceDocument
  -> SourceChunk
  -> Claim
  -> Concept
  -> KnowledgeBlock
  -> proposal or canonical write
```

自我迭代路径：

```text
run / ingest / query result
  -> lint and gates
  -> evals
  -> proposal
  -> apply or rollback
  -> index rebuild
  -> log entry
```

## CLI 参考

校验：

```bash
evolvekb validate --settings settings/evolve.yaml
evolvekb kb lint --gate-level 2
```

知识与检索：

```bash
evolvekb ingest README.md
evolvekb ingest README.md --proposal
evolvekb query "execution-first knowledge runtime"
```

Playbooks 与 skills：

```bash
evolvekb run --intent compare_frameworks --question "对比 GraphRAG 和 Execution-first"
evolvekb run --intent answer_with_evidence --question "What is execution-first knowledge?"
evolvekb skills list
evolvekb skills inspect compare-frameworks
```

演进工作流：

```bash
evolvekb evolve doc README.md --settings settings/evolve.yaml --eval "evals/*.yaml"
evolvekb proposal list
evolvekb proposal apply <proposal-id-or-path>
evolvekb proposal rollback <proposal-id>
```

Index、log 与 evals：

```bash
evolvekb kb index
evolvekb kb log note "Reviewed a knowledge update"
evolvekb eval run "evals/*.yaml"
```

## 项目结构

```text
evolvekb/
  assets/       # frontmatter、loading、registry、hashing
  core/         # pydantic models 和 settings
  evals/        # YAML eval runner
  evolution/    # proposal create/apply/rollback
  gates/        # validation gates
  ingestion/    # deterministic markdown compiler
  retrieval/    # keyword retrieval as evidence supply
  skills/       # skill registry 和 playbook runtime
kb/
  index.md      # 生成的 KB map
  log.md        # 追加式演进日志
  knowledge/    # canonical knowledge assets
  usage/        # canonical usage assets
skills/         # SKILL.md playbooks 和 procedures
settings/       # mode presets
evals/          # eval cases
examples/       # 可运行示例和期望输出
scripts/        # legacy wrappers
tests/          # pytest suite
```

Schema 细节见 [kb/SCHEMA.md](kb/SCHEMA.md)。

## 自我迭代模型

EvolveKB 参考了 Karpathy 的 LLM Wiki pattern：保持 raw sources 稳定，维护模型写出的 markdown，用 index 和 log 帮助模型理解当前知识库，并周期性 lint。

EvolveKB 将这个思路 runtime 化：

- Knowledge 和 usage 是分离的资产。
- Skills 是可执行的，并按 intent 路由。
- Retrieval 提供证据，但不定义整个系统。
- Proposals 是可审阅事务，不是静默写入。
- Gates 和 evals 决定更新是否足够安全。

参考说明：[Karpathy LLM Wiki comparison](docs/karpathy-llm-wiki-comparison.md)

## 示例

对比 playbook：

```bash
evolvekb run \
  --intent compare_frameworks \
  --question "对比 GraphRAG 和 Execution-first"
```

证据优先回答：

```bash
evolvekb run \
  --intent answer_with_evidence \
  --question "What is execution-first knowledge?"
```

Eval smoke suite：

```bash
evolvekb eval run "evals/*.yaml"
```

参考：

- [examples/demo.md](examples/demo.md)
- [examples/evidence_answer.md](examples/evidence_answer.md)

## 开发

安装开发依赖：

```bash
python -m pip install -e ".[dev]"
```

运行检查：

```bash
pytest -q
ruff check evolvekb tests scripts
python -m evolvekb.cli validate --settings settings/evolve.yaml
python scripts/validate.py --settings settings/evolve.yaml
python -m evolvekb.cli eval run "evals/*.yaml"
```

当前测试覆盖 settings、frontmatter parsing、Pydantic models、asset registry、gates、skill routing、runtime execution、ingestion、retrieval、proposals、evals、CLI commands 和 legacy wrappers。

## 路线图

已完成：

- README 和产品定位。
- Settings presets 和 mode-aware output。
- 最小 end-to-end demo。
- Package runtime 和 CLI。
- Schema v2 和 AssetRegistry。
- KB index/log 与 lintable self-iteration loop。
- Gate evolution loop。
- Claim/evidence ingestion compiler。
- Proposal apply/rollback workflow。
- Eval harness 与 retrieval-as-evidence。
- 新增 playbook：`answer-with-evidence`。

下一步：

- HTTP API 和 proposal review UI。
- LLM-backed claim extraction。
- Contradiction 和 supersession checks。
- Hybrid retrieval：keyword + semantic + graph。
- 更大的 eval corpus。
- 更多领域 playbooks 和 examples。

## License

See [LICENSE](LICENSE).
