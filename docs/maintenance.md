# Maintenance and roadmap

Last reviewed: **2026-11-16**. Source baseline: [`28af622`](https://github.com/2sao7sao/EvolveKB/commit/28af62288593b5986d79a593bafe67ad81964709).

[English README](../README.md) · [中文 README](../README.zh.md) · [Contributing](../CONTRIBUTING.md)

## Maintenance recommendation

Continue maintaining the local prototype, with documentation and release hygiene
as the next scope. The main branch last changed on 2026-09-04. At this review there
were no open issues or pull requests; inactivity alone is not an archive criterion.
Keep feature additions tied to a reproducible failure case and an acceptance check.

This page records a dated review. It is not a promise of a release date or a claim
that all planned versions have shipped.

## Verified in this review

| Check | Observed result | Scope |
| --- | --- | --- |
| `python -m pytest -q` | 97 passed | Local Python 3.12.6 run at the baseline above. |
| `python -m evolvekb.cli demo` | PASS | Synthetic refund policy: 5/5 grounded claims, 2/2 demo evals, 1/1 proposal gate. |
| `python -m evolvekb.cli eval run "evals/*.yaml"` | 12/12 passed | Repository seed cases only. |
| `python -m evolvekb.cli validate --settings settings/evolve.yaml` | Passed, `no gates evaluated` | A clean checkout has no generated claims/proposals to scan. |
| Main branch CI | [Successful run](https://github.com/2sao7sao/EvolveKB/actions/runs/33849102162) on 2026-09-04 | Historical GitHub run, separate from the local checks above. |

The package declared `0.3.0` at this review; the GitHub Releases list and git tags were empty then.
[`v0.4.0`](https://github.com/2sao7sao/EvolveKB/releases/tag/v0.4.0) on 2026-11-18 is the first tag,
and the version badge follows the package version.

## Implemented foundations and remaining work

The previous roadmap grouped these features under v0.4–v0.6. The foundations are
already present, so future work should address the remaining acceptance gaps.

| Foundation | Evidence | Still incomplete |
| --- | --- | --- |
| EvidencePack and pluggable retrieval | [Retrieval contract](RETRIEVAL.md), [registry tests](../tests/retrieval/test_pluggable_retriever.py) | Broader retrieval-quality evaluation beyond deterministic local seeds. |
| Step-level execution traces | [Trace contract](RUNTIME_TRACE.md), [trace tests](../tests/skills/test_runtime_trace.py) | Evidence from an external agent integration. |
| Python procedure entrypoints | [Executor tests](../tests/skills/test_python_executor.py) | `PROC_IMPL` compatibility fallback remains; executor dispatch currently supports Python only. |
| Eval matrix and proposal review | [Eval matrix tests](../tests/evals/test_eval_matrix.py), [impact tests](../tests/proposals/test_proposal_impact.py) | Broader domain/failure cases and further rollback edge cases. |

No current result establishes production readiness, general semantic-search
superiority, or performance across arbitrary agent workloads.

## Next tasks

| Priority | Task | Acceptance evidence |
| --- | --- | --- |
| P1 | Add missing-evidence and conflicting-policy cases | Public or synthetic input, explicit expected behavior, separate reported result for each failure case. |
| P1 | Inventory and migrate remaining `PROC_IMPL` callers | List each caller, declare its runtime entrypoint, and verify equivalent outputs and traces before removing fallback code. |
| P1 | Extend proposal rollback coverage | Add one hash-conflict or partial-change fixture; inspect the resulting state and prove unrelated files stay intact. |
| P2 | Decide the release and optional Pages scope | Align source version/changelog with accepted capabilities; publish only after the selected delivery path is verified. |

Documentation work in this maintenance pass removes the unavailable Product Page
entrypoint, aligns both READMEs with implemented foundations, and labels the static
terminal image and seed metrics. These edits do not change runtime behavior.

## Pages and visual assets

The Pages API returned 404 during this review. The [Pages workflow](../.github/workflows/pages.yml)
is manual-only and documents the previous deployment failure. Repository
walkthroughs are the current documentation entrypoint. If a hosted page becomes
necessary, configure Pages, deploy it, verify the URL, then restore the navigation link.

The README banner is a project identity/flow illustration. The
[terminal image](assets/evolvekb-demo-terminal.svg) is reconstructed CLI output;
its source of truth is `python -m evolvekb.cli demo`, not pixels or hardcoded
README values. [Provenance and refresh instructions](assets/README.md).

Legacy `assets/banner.png`, `assets/architecture.svg`, and `assets/mode_matrix.svg`
had no text references in the checked tree. Keep them until their history and any
external use are reviewed; they are not part of the current README sequence.

## 中文摘要

建议继续维护本地原型，先收敛文档与发布入口。当前基础能力可复验，旧路线中的多项功能
已有实现，但不能据此声称未来版本已完整发布。下一步聚焦：缺失证据/冲突政策用例、
旧 procedure fallback 的兼容迁移、回滚边界测试，以及单独的发布决策。
本轮 97 个测试与 12 个 eval 种子用例通过，仅证明本地确定性范围；外部 Agent 与生产验收仍未建立。

## Brand assets

Both language editions use the same 1600 × 600 hero, shared seated penguin, and project-specific accent and symbol. [Asset inventory and provenance](../assets/brand/README.md). Existing technical figures remain separate from brand artwork.

## Tracked follow-up

[Next milestone / 下一阶段任务 #13](https://github.com/2sao7sao/EvolveKB/issues/13) contains the actionable checklist. The maintenance PR [hosted CI](https://github.com/2sao7sao/EvolveKB/actions/runs/43888828759) passed on 2026-11-16 at `9675a4f`; historical runtime and provider results retain their original scope.
