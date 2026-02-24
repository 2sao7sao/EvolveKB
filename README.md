# NewKnowledgeBase — Skills-driven Knowledge Base (Execution-First)

> 一个把“知识”组织成 **可执行技能（skills）** 的知识库框架：  
> 不止做 recall/rerank，而是把知识沉淀为 **可复用的流程（playbook）与过程（procedure）**，并用门控机制推动知识持续演进。

---

## What problem this solves

传统 RAG 的常见路径是：

- query → recall（召回 chunk）→ rerank → LLM 参考候选内容生成

它工程成熟，但长期存在三类痛点：

- **知识未被真正理解**：模型多在“候选片段附近”拼接，而不是通读与结构化理解。
- **multi-hop 易断链**：chunk 切分导致跨段逻辑丢失，上下文被拆散。
- 即便 GraphRAG / RAPTER 做预处理联结，本质仍是为了更好召回。

本仓库探索的路线是：

> **Execution-first**：把知识升级为“可执行的技能”，  
> 让 agent 在系统内完成：理解、梳理、更新、演进，甚至自推演探索补充。  
> 最终让知识库“更懂你”，并从根源产出可用信息，而不是依赖候选池参考。

---

## Core concepts (you only need these 4)

### 1) Skill = Playbook / Procedure
- **Playbook**：面向一个 intent 的完整工作流（由多个步骤组成）
- **Procedure**：可复用的原子能力（被多个 playbook 调用）

### 2) Knowledge usage modes (user-selectable)
不同用户对“上传内容如何被使用”的偏好不同。本项目将“知识的用法”做成可配置策略：

- **Reference Mode（引用型）**：更像 RAG，只在需要时引用资料，不强行改写知识库
- **Digest Mode（消化型）**：模型先做结构化摘要/要点/术语表，再用于回答
- **Transform Mode（转化型）**：把知识转为 procedures/playbooks（可执行技能）
- **Evolve Mode（演进型）**：允许模型在门控下提出改动，形成版本化更新

> 目标：让用户明确选择“知识如何参与推理与产出”，避免一刀切。

### 3) Settings Layer (config)
把“知识用法/门控强度/演进策略”从代码和 prompt 中抽离出来，形成一个设置层。

- 你可以把它理解为：**这是知识库的“操作系统设置”**。
- 同一套知识，在不同 settings 下会表现出不同的行为（更保守 / 更积极 / 更结构化）。

> TODO: 后续可引入 `settings/` 或 `config.yaml`（见 Roadmap）

### 4) Gates (quality control for evolution)
知识演进必须可控，否则会“越改越乱”。本仓库强调“先门控，再扩展”：

- Gate 负责：结构正确、引用完整、内容瘦身、可回滚、可验证
- Gate 不只是规则集合，也是可进化对象（见下文）

---

## How it works (high level)

1) 用户提供问题 / 上传内容  
2) 系统按 settings 选择知识使用模式（reference/digest/transform/evolve）  
3) 路由到对应 playbook  
4) playbook 调用 procedures 分步执行  
5) 每一步都能在门控下产出“可验证中间产物”  
6) 若开启 evolve：提出变更 → 通过 gate → 合并为知识库新版本

---

## Repository structure

```text
skills/
  <skill-name>/
    SKILL.md        # YAML frontmatter + markdown body
scripts/
  validate.py       # repo-level checks (symlinks, size limits, etc.)
  skill_validate.py # validates skills: schema, naming, playbook/procedure refs
  run.py            # minimal runner: route by intent -> execute playbook/procedures
AGENT.md            # gate rules / slimming constraints / authoring rules
USER.md             # user-facing usage guidance
```

---

## Quickstart

```bash
python -m pip install -r requirements.txt
python scripts/validate.py
python scripts/run.py --intent compare_frameworks --question "对比 GraphRAG 和 md-knowledge 的差异"
```

---

## Skill format (SKILL.md)

每个 skill 都由两部分构成：

1) YAML frontmatter（强校验：结构化元信息）  
2) Markdown body（人类可读：保持精简，长资料下沉）

### Playbook example

```yaml
---
name: compare-frameworks
description: Compare two frameworks and output a structured decision memo.
allowed-tools: []
metadata:
  kind: playbook
  intent: compare_frameworks
  steps:
    - id: normalize
      uses: normalize-question
    - id: compare
      uses: compare-frameworks
---
```

### Procedure example

```yaml
---
name: normalize-question
description: Normalize user question into structured requirements.
allowed-tools: []
metadata:
  kind: procedure
  inputs:
    question: string
  outputs:
    normalized_question: string
---
```

---

## Settings (planned design)

> 你提出的关键：用户可自行设置“知识的用法”。

建议后续引入配置文件，例如：

- `settings/default.yaml`
- `settings/profile_minimal.yaml`
- `settings/profile_evolve.yaml`

配置内容先做到“够用”，例如：

- `knowledge_mode`: reference | digest | transform | evolve
- `gate_level`: 0..3（越高越严格）
- `auto_evolve`: true/false（是否允许自动提出 PR）
- `max_skill_md_bytes`: 50000（瘦身门槛）
- `allowed_tools`: [...]（工具白名单）
- `memory_policy`: conservative | balanced | aggressive（如何吸收新知识）

> TODO: `run.py` 支持 `--settings settings/default.yaml`

---

## Gates are not fixed (they should evolve)

你的观点：

> 人类一开始设计的框架未必最合理，但能加快落地；  
> 随着积累，系统应该把反馈用于 **升级门控机制** 与 **升级知识框架**，而不是永远停在最初的规则里。

因此建议把 gate 的演进也纳入闭环：

- 初期：人类定义 Gate（快速落地、可控）
- 中期：模型在 Gate 下演进知识，并产出“失败样例/边界案例”
- 后期：系统根据这些案例反过来改进 Gate 与 Schema  
  （例如：新增字段、增强校验、优化 slimming 策略、增加回归测试）

> 方向：让 gate 从“人工规则”逐步变成“数据/反馈驱动的规则”。

---

## Roadmap (beginner-friendly)

1) ✅ README / docs 可读性（当前）
2) ⏭️ 引入 settings 文件，让用户可选知识使用模式（reference/digest/transform/evolve）
3) ⏭️ 上 CI：每次提交自动跑 `python scripts/validate.py`
4) ⏭️ 扩展 skill schema（version/owner/tags/examples）+ 更严格校验
5) ⏭️ 引入可插拔执行层（tool/llm executor），替换 placeholder
6) ⏭️ 加入“gate evolution loop”：基于失败案例持续升级 gate 与框架

---

## Contributing (self workflow)

每次只做一个小改动，保证可回滚：

```bash
git checkout main
git pull
git checkout -b chore/readme-improve

# edit README.md

git add README.md
git commit -m "Improve README: settings + gates evolution"
git push -u origin chore/readme-improve
```

在 GitHub 点 **Compare & pull request** 创建 PR，无误后 Merge。

---

## License

See `LICENSE`.
