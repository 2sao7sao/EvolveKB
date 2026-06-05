<img src="assets/readme-banner.svg" alt="EvolveKB banner" width="100%" />

<p align="center">
  <a href="./README.md">English</a>
  ·
  <a href="https://2sao7sao.github.io/EvolveKB/">产品首页</a>
  ·
  <a href="./examples/evolution_loop.md">核心 Demo</a>
  ·
  <a href="./examples/customer_support_refund_agent.md">Support Agent 示例</a>
  ·
  <a href="./CONTRIBUTING.md">贡献指南</a>
</p>

<p align="center">
  <a href="https://github.com/2sao7sao/EvolveKB/actions/workflows/ci.yml"><img src="https://github.com/2sao7sao/EvolveKB/actions/workflows/ci.yml/badge.svg?branch=main" alt="CI"></a>
  <img src="https://img.shields.io/badge/python-3.11%2B-ff5aa5" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/version-v0.3.0-b8eee4" alt="version v0.3.0">
  <img src="https://img.shields.io/badge/license-Apache--2.0-ff5aa5" alt="Apache-2.0 license">
</p>

# EvolveKB

**Agent 知识运行时：把文档变成可执行、可验证、可演进的 Agent 知识资产。**

RAG 解决的是“找到相似文本”。EvolveKB 追问的是另一个更贴近 Agent 落地的问题：

> 这份文档能不能变成 Agent 可以执行、测试、评审，并在真实使用后安全更新的行为？

如果你的 Agent 依赖政策、SOP、runbook、研究笔记或工程规范，单纯把 chunk
塞进 prompt 不够。系统需要 claims、evidence、usage playbook、skill contract、
validation gate、regression eval，以及可评审的知识更新流程。

![EvolveKB terminal demo](docs/assets/evolvekb-demo-terminal.svg)

## 30 秒产品路径

```text
Document
  -> grounded claims
  -> typed knowledge asset
  -> usage playbook
  -> SKILL.md procedure
  -> validation gates
  -> regression evals
  -> reviewable proposal
```

| 如果你有... | EvolveKB 让 Agent 得到... |
| --- | --- |
| 政策文档 | 带证据的规则、例外和约束 |
| SOP / runbook | 可复用 playbook，而不是 prompt 堆料 |
| 内部方法论 | 什么时候用、如何用的 usage guidance |
| 知识漂移 | gates、evals、proposals 和 rollback 路径 |
| Agent harness | skills、evidence、governance 的运行时接口 |

## 这个仓库包含什么

| Surface | 作用 |
| --- | --- |
| Runtime | demo、validate、query、run、ingest、eval 等 CLI 命令。 |
| Knowledge assets | typed Markdown claims、source evidence、usage assets 和 evolution log。 |
| Skills | 把知识变成可重复行为的 `SKILL.md` procedures。 |
| Gates | 知识变更落地前的结构、命名、证据、打包和安全检查。 |
| Evals | 覆盖 retrieval、routing、evidence use 和 playbook coverage 的回归种子。 |
| Product docs | 解释 execution-first knowledge model 的 GitHub Pages 和示例。 |

## 5 分钟跑通 Demo

```bash
git clone https://github.com/2sao7sao/EvolveKB.git
cd EvolveKB
python -m pip install -e ".[dev]"
python -m evolvekb.cli demo
```

Demo 会在临时 workspace 中运行，不污染当前仓库。它会摄取一份合成退款政策，
抽取带证据的 claims，生成待评审 proposal，运行 gates 和 regression evals，
最后输出产品指标。

输出形态如下：

```text
# EvolveKB Flagship Demo

status: PASS

## 1. Ingest policy into knowledge assets
- claims: 5
- grounded_claims: 5
- proposal: kb/proposals/...

## 3. Product metrics
- claim_grounding_rate: 1.00 (5/5)
- playbook_success_rate: 1.00 (2/2)
- proposal_gate_pass_rate: 1.00 (1/1)
- retrieval_vs_playbook_delta: 0.80 (4/5)
```

`retrieval_vs_playbook_delta` 是 seed-level capability coverage，不是大规模 benchmark
结论。完整 checklist 见 [docs/METRICS.md](docs/METRICS.md)。
如果你更喜欢直接看脚本，可以运行 `examples/run_evolution_loop.py`，它和 CLI demo
走同一条产品路径。

如果你想看更具体的客服场景，可以运行：

```bash
python examples/customer_support_refund_agent.py
```

## 它为什么不只是 RAG

| 问题 | 纯检索知识库 | EvolveKB |
| --- | --- | --- |
| 能否找到相关文本 | 可以 | 可以 |
| 知识是否有 typed claims 和 evidence | 通常没有 | 有 |
| 系统是否知道知识该如何使用 | 通常没有 | usage playbooks |
| 工作流是否能作为可重复 skill 执行 | 不能 | `SKILL.md` procedures |
| 更新是否能被 gate 和 review | 很少 | proposals + validation |
| 行为回归是否能被测试 | 很少 | eval seeds + runtime checks |

> [!NOTE]
> 默认检索后端是 deterministic keyword retrieval，同时提供 BM25、deterministic
> semantic-lite 和 hybrid 模式用于本地实验。EvolveKB v0.3 不声明广义语义检索
> 能力优于 RAG，而是把重点放在“知识是否可操作”：可使用、可测试、可评审、可安全演进。

## 指标不是装饰

Demo 指标来自实际运行产物，不是手工写在 README 里的展示数字。公式、分子、
分母和当前 retrieval-only baseline 见 [docs/METRICS.md](docs/METRICS.md)。

| 指标 | 衡量什么 | 当前来源 |
| --- | --- | --- |
| `claim_grounding_rate` | 抽取出的 claims 是否保留 source evidence | `evolvekb.ingestion.compiler` |
| `playbook_success_rate` | routing/retrieval seed eval 是否通过 | `evolvekb.evals.runner` |
| `proposal_gate_pass_rate` | proposal 生成后仓库 gates 是否仍然通过 | `evolvekb.demo` + `evolvekb.gates` |
| `retrieval_vs_playbook_delta` | 相比纯检索，执行式链路多覆盖了哪些 seed-level 能力 | `evolvekb.demo.CAPABILITY_COVERAGE_CHECKLIST` |

直接运行 regression seed：

```bash
python -m evolvekb.cli eval run "evals/*.yaml"
```

## 开发者接口

贡献者常用文档：

| 文档 | 用途 |
| --- | --- |
| [指标定义](docs/METRICS.md) | 解释 demo 公式和 `retrieval_vs_playbook_delta` checklist。 |
| [Retrieval contract](docs/RETRIEVAL.md) | 说明 EvidencePack、keyword/BM25/hybrid modes 和 eval mode selection。 |
| [Runtime trace](docs/RUNTIME_TRACE.md) | 说明 step-level RunTrace JSON 和 CLI trace output。 |
| [Proposal review](docs/PROPOSAL_REVIEW.md) | 说明 impact metadata、rollback plan、safety assessment 和 gates。 |
| [Skill 模板](docs/SKILL_TEMPLATE.md) | 新增 procedure/playbook 时的注释版 `SKILL.md` 起点。 |
| [Support agent 示例](examples/customer_support_refund_agent.md) | 带 evidence IDs 和 trace id 的端到端退款政策工作流。 |
| [Starter issues](docs/STARTER_ISSUES.md) | 适合作为第一单 PR 的小任务。 |
| [Demo 图片来源](docs/assets/README.md) | 说明 terminal 图片如何生成和刷新。 |

```bash
# 验证 knowledge、usage assets、skills 和 gate constraints
python -m evolvekb.cli validate --settings settings/evolve.yaml

# 从 knowledge assets 和 compiled claims 查询证据
python -m evolvekb.cli query "execution-first knowledge runtime" --retriever keyword --require-evidence

# 使用同一个 EvidencePack contract 尝试本地 BM25 检索
python -m evolvekb.cli query "execution-first knowledge runtime" --retriever bm25 --require-evidence

# 运行知识驱动 playbook
python -m evolvekb.cli run \
  --intent compare_frameworks \
  --question "Compare GraphRAG vs Execution-first" \
  --settings settings/reference.yaml \
  --no-side-effects

# 从文档生成可评审 proposal
python -m evolvekb.cli ingest examples/refund_policy.md --proposal
```

最小 harness 接入示例：

```python
from pathlib import Path

from evolvekb.skills.runtime import PlaybookRuntime

runtime = PlaybookRuntime(Path("."))
result = runtime.run(
    intent="answer_with_evidence",
    question="What does the KB say about execution-first knowledge?",
    settings_arg="settings/reference.yaml",
    write_side_effects=False,
)
print(result.rendered)
print(result.trace.id)
```

## 架构

```mermaid
flowchart LR
  A["Source docs"] --> B["Ingestion compiler"]
  B --> C["Claims + evidence"]
  B --> D["Knowledge assets"]
  D --> E["Usage playbooks"]
  E --> F["SKILL.md procedures"]
  F --> G["Playbook runtime"]
  G --> H["Validation gates"]
  H --> I["Regression evals"]
  I --> J["Reviewable proposals"]
  J --> D
```

## 稳定能力与原型边界

| 层 | 当前状态 |
| --- | --- |
| Asset schemas | 足够支撑本地实验和示例 |
| CLI demo、validate、query、run、ingest、eval | 当前支持的产品路径 |
| Proposal creation / rollback | 支持本地文件 |
| Keyword/BM25 retrieval | 基于共享 [EvidencePack contract](docs/RETRIEVAL.md) 的本地 lexical baseline |
| Procedure implementations | deterministic MVP 示例，不是完整 skill marketplace |
| Benchmark claims | seed-level proof，不是大规模 RAG 替代 benchmark |

## 适合 / 不适合

适合：

| 场景 | 原因 |
| --- | --- |
| Agent 政策和 SOP | 知识需要触发受控行为 |
| 客服、合规、运维 playbook | 回答需要证据、路由和审批 |
| 研究到实践的方法论 | 隐藏用法比相似 chunk 更重要 |
| 事故后持续演进的 runbook | 实践结果应该通过 review 更新知识 |

不适合：

| 场景 | 更合适的方案 |
| --- | --- |
| 一次性文档问答 | 普通 RAG 更快 |
| 纯语义搜索 | vector / hybrid retrieval |
| 用户记忆和个性化 | 需要带隐私控制的 memory system |
| 未评审的自动写入 | 先增加 human review 和 approval gates |

## 仓库结构

```text
evolvekb/       runtime、CLI、demo metrics、gates、ingestion、retrieval、evals
kb/             knowledge assets、usage assets、index、evolution log
skills/         可执行 SKILL.md playbooks 和 procedures
settings/       reference、digest、transform、evolve 预设
evals/          retrieval、routing、capability coverage seeds
examples/       可运行 demo 输入和产品 walkthrough
docs/           产品首页和补充说明
```

## Roadmap

| Release track | Focus | Exit criteria |
| --- | --- | --- |
| v0.3.x | trust、docs、metrics、first contribution path | version 对齐、CI badge、METRICS.md、SKILL_TEMPLATE.md、customer support example |
| v0.4.x | evidence contract、pluggable retrieval、runtime trace | [EvidencePack](docs/RETRIEVAL.md)、keyword/BM25 adapters、step-level RunTrace、trace CLI |
| v0.5.x | dynamic skill execution engine | runtime entrypoints、executor registry、legacy `PROC_IMPL` fallback deprecated |
| v0.6.x | eval matrix 与 proposal impact review | baseline comparison evals、proposal impact metadata、rollback reports |

## Security

不要提交私有文档、API key、token、客户 trace，或包含敏感信息的 proposal 输出。
见 [SECURITY.md](SECURITY.md)。

## License

Apache-2.0. See [LICENSE](LICENSE).
