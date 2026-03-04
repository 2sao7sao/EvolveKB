<img src="assets/banner.png" alt="banner" width="100%" />

# EvolveKB — Your Execution‑First Knowledge Companion

[![Status](https://img.shields.io/badge/status-Concept%20%2F%20WIP-yellow)](./README.md)
[![Stars](https://img.shields.io/github/stars/2sao7sao/EvolveKB?style=flat)](https://github.com/2sao7sao/EvolveKB)
[![License](https://img.shields.io/badge/license-MIT-blue)](./LICENSE)

> 把“知识”变成 **可执行的技能**。  
> 不是简单存文档，而是让 AI 学会 **你的知识使用逻辑**，并在门控下持续演进。

---

## Quick links

- [Vision](#vision)
- [Use cases](#use-cases)
- [How it works](#how-it-works)
- [Roadmap](#roadmap)

---

## TL;DR

- 一个“外挂知识库”：重点是**知识使用逻辑**，而不是存储介质。
- 支持 **引用 / 消化 / 转化 / 演进** 四种用法，按你的习惯参与推理。
- 目标是让 AI **更懂你要什么知识、如何存、怎么用才有效**。

---

## Vision

**Execution‑first**：先让知识可执行，再谈召回增强。  
我们希望 AI 不只是“找得到资料”，而是“知道如何组织与使用资料”。

当前状态：**Concept / WIP**（偏产品方向探索，尚未形成稳定可用的工程版本）。

---

## Why (问题是什么)

传统 RAG 更擅长“找资料”，不擅长“让资料变成可复用流程”：

- **理解浅**：多是片段拼接，而非结构化理解与沉淀。
- **multi‑hop 易断链**：chunk 切分导致跨段逻辑断裂。
- **用法单一**：同一知识对不同用户/任务缺乏可配置的使用策略。

---

## What (我们提供什么)

**EvolveKB = 把知识升级为技能**：

- **Playbook**：面向一个 intent 的完整流程
- **Procedure**：可复用的原子能力
- **Settings**：控制知识如何参与推理与产出
- **Gate**：质量控制与演进门控

---

## Use cases

- **摒弃纯向量库路径**：不依赖“只做召回”，而是让知识可执行。
- **持续演进的知识更新**：在门控下沉淀更新，形成可回滚的版本演进。
- **更懂你的知识习惯**：通过交互学习你希望“如何存、怎么用、何时更新”。

---

## How it works

1. 用户提问 / 上传资料
2. 读取 settings：选择知识使用模式（reference / digest / transform / evolve）
3. 路由到对应 playbook
4. playbook 调用 procedures 分步执行
5. 每一步在 gate 下生成可验证中间产物
6. 若开启 evolve：提出变更 → gate 审核 → 合并为知识库新版本

---

## Knowledge usage modes

| Mode | 作用 | 典型场景 |
| --- | --- | --- |
| Reference | 仅引用资料，不改写知识库 | 快速问答 / 保守模式 |
| Digest | 结构化摘要后再回答 | 需要吸收与总结 |
| Transform | 转为 procedures/playbooks | 构建可复用技能 |
| Evolve | 允许提出变更并门控合并 | 持续演进知识库 |

---

## Roadmap

1. ✅ README / 产品叙事定稿
2. ⏭️ 引入 settings 文件，用户可选知识使用模式
3. ⏭️ 定义核心 skill schema 与 gate 规则
4. ⏭️ 实现最小可运行 demo（一条 end‑to‑end 路径）
5. ⏭️ 引入“gate evolution loop”

---

## Star history

![Star History](https://api.star-history.com/svg?repos=2sao7sao/EvolveKB&type=Date)

---

## License

See `LICENSE`.
