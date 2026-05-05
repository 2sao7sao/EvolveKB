from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
import re

import yaml

from evolvekb.assets.frontmatter import parse_frontmatter
from evolvekb.core.config import Settings, load_settings
from evolvekb.retrieval.keyword import evidence_pack
from evolvekb.skills.registry import SkillRegistry
from evolvekb.wiki import append_kb_log


def normalize_question(question: str) -> dict[str, Any]:
    targets: list[str] = []
    for token in ["graphrag", "rag", "md", "knowledge", "skills", "mcp", "function call", "openclaw"]:
        if token.lower() in question.lower():
            targets.append(token)
    intent_hint = "compare_frameworks" if ("对比" in question or "compare" in question.lower()) else "unknown"
    return {"intent_hint": intent_hint, "targets": targets, "constraints": [], "raw": question}


def build_comparison_axes(norm: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {"axis": "index_time_synthesis", "why_matters": "建库阶段是否先综合/抽象"},
        {"axis": "query_time_cost", "why_matters": "查询时成本/延迟/稳定性"},
        {"axis": "governance", "why_matters": "可审计、可回滚、防漂移"},
        {"axis": "multi_hop", "why_matters": "多跳路径是否稳定可解释"},
        {"axis": "maintenance", "why_matters": "维护复杂度转移（索引结构 vs 知识工程）"},
    ]


def contrast_matrix(norm: dict[str, Any], axes: list[dict[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for item in axes:
        axis = item["axis"]
        if axis == "index_time_synthesis":
            out.append(
                {
                    "axis": axis,
                    "A": "抽实体/关系 + 社区摘要",
                    "B": "编译为可调用procedures/playbooks",
                    "tradeoff": "两者都前置综合；B强调执行语义与治理",
                }
            )
        elif axis == "query_time_cost":
            out.append(
                {
                    "axis": axis,
                    "A": "检索/遍历/拼上下文",
                    "B": "入口→步骤执行，更稳定",
                    "tradeoff": "A更灵活；B要求入口覆盖",
                }
            )
        elif axis == "governance":
            out.append(
                {
                    "axis": axis,
                    "A": "索引管线治理为主",
                    "B": "Git/PR+Gate，知识资产一等公民",
                    "tradeoff": "B更适合工程迭代",
                }
            )
        elif axis == "multi_hop":
            out.append(
                {
                    "axis": axis,
                    "A": "图结构辅助证据连接",
                    "B": "playbook显式编排多步",
                    "tradeoff": "B路径稳定，但需要维护契约",
                }
            )
        else:
            out.append({"axis": axis, "A": "图/索引维护", "B": "知识模块/门控维护", "tradeoff": "复杂度转移"})
    return out


def compose_answer_md(norm: dict[str, Any], matrix: list[dict[str, str]]) -> str:
    lines: list[str] = []
    lines.append("# 对比：GraphRAG vs Execution-first Markdown Knowledge\n")
    lines.append("你选择的是 **执行式知识编译**：用 procedures/playbooks 取代“检索碎片”。\n")
    lines.append("| 维度 | GraphRAG | Execution-first MD | 权衡 |")
    lines.append("|---|---|---|---|")
    for row in matrix:
        lines.append(f"| {row['axis']} | {row['A']} | {row['B']} | {row['tradeoff']} |")
    lines.append("\n## 建议\n- 闭域可枚举入口：execution-first 更稳。\n- 开放域入口不可枚举：GraphRAG 弹性更强。")
    return "\n".join(lines)


def retrieve_evidence(repo: Path, query: str, limit: int = 5) -> dict[str, Any]:
    return evidence_pack(repo, query, limit=limit)


def compose_evidence_answer(question: str, evidence: dict[str, Any]) -> str:
    lines = ["# Evidence-backed answer\n", f"Question: {question}", "", "## Evidence"]
    items = evidence.get("evidence") or []
    if not items:
        lines.append("- No matching evidence found.")
    for item in items:
        lines.append(f"- `{item['name']}` ({item['source_ref']}): {item['text']}")
    lines.extend(["", "## Answer", "Use the evidence above as grounded context before drafting a final response."])
    return "\n".join(lines)


def extract_outline(doc_path: str) -> dict[str, Any]:
    path = Path(doc_path)
    if not path.exists():
        raise SystemExit(f"Document not found: {doc_path}")
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = [line.rstrip() for line in text.splitlines()]
    headings: list[dict[str, Any]] = []
    for line in lines:
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            title = line.lstrip("#").strip()
            if title:
                headings.append({"level": level, "title": title})

    summary = ""
    buf: list[str] = []
    for line in lines:
        if line.strip() == "":
            if buf:
                summary = " ".join(buf).strip()
                break
            continue
        if not line.startswith("#") and not line.lstrip().startswith("<"):
            buf.append(line.strip())
    if not summary and buf:
        summary = " ".join(buf).strip()
    return {"headings": headings, "summary": summary, "doc_name": path.stem, "doc_path": str(path)}


def compose_skill_draft(outline: dict[str, Any]) -> str:
    doc_name = outline.get("doc_name") or "doc"
    name = f"ingest-{doc_name}".lower().replace("_", "-").replace(" ", "-")
    headings = outline.get("headings") or []
    summary = outline.get("summary") or ""
    body_lines = [f"# {name} (procedure)", "", "## Summary", summary or "N/A", "", "## Outline"]
    if headings:
        for heading in headings:
            indent = "  " * max(0, int(heading.get("level", 1)) - 1)
            body_lines.append(f"{indent}- {heading.get('title')}")
    else:
        body_lines.append("- (no headings found)")
    fm = [
        "---",
        f"name: {name}",
        f"description: Ingest and structure knowledge from {doc_name}.",
        "metadata:",
        "  kind: procedure",
        "  inputs:",
        "    doc_path: str",
        "  outputs:",
        "    outline: list",
        "    summary: str",
        "---",
        "",
    ]
    return "\n".join(fm + body_lines) + "\n"


def compose_knowledge_md(outline: dict[str, Any]) -> str:
    doc_name = outline.get("doc_name") or "doc"
    doc_path = outline.get("doc_path") or doc_name
    name = f"{doc_name}".lower().replace("_", "-").replace(" ", "-")
    headings = outline.get("headings") or []
    summary = outline.get("summary") or ""
    concepts = [heading.get("title") for heading in headings[:8] if heading.get("title")]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    fm_dict = {
        "schema_version": 2,
        "id": f"kb_{name.replace('-', '_')}",
        "name": name,
        "kind": "knowledge",
        "block_type": "reference",
        "source_refs": [{"source_id": doc_path, "chunk_ids": []}],
        "summary": summary or "N/A",
        "claims": [],
        "concepts": concepts,
        "confidence": 0.5,
        "recommended_usage": [],
        "tags": [],
        "updated_at": today,
        "version": 1,
        "status": "active",
    }
    fm_yaml = yaml.safe_dump(fm_dict, sort_keys=False, allow_unicode=True).strip()
    body = [f"# {doc_name}", "", "## Notes", summary or "N/A"]
    return "\n".join(["---", fm_yaml, "---", ""] + body) + "\n"


ProcedureImpl = Callable[[dict[str, Any], dict[str, Any]], Any]

PROC_IMPL: dict[str, ProcedureImpl] = {
    "normalize-question": lambda env, args: normalize_question(args["question"]),
    "build-comparison-axes": lambda env, args: build_comparison_axes(args["norm"]),
    "contrast-matrix": lambda env, args: contrast_matrix(args["norm"], args["axes"]),
    "compose-answer-md": lambda env, args: compose_answer_md(args["norm"], args["matrix"]),
    "extract-outline": lambda env, args: extract_outline(args["doc_path"]),
    "compose-skill-draft": lambda env, args: compose_skill_draft(args["outline"]),
    "compose-knowledge-md": lambda env, args: compose_knowledge_md(args["outline"]),
    "retrieve-evidence": lambda env, args: retrieve_evidence(
        Path(str(env["repo"])), args["query"], int(args.get("limit", 5))
    ),
    "compose-evidence-answer": lambda env, args: compose_evidence_answer(
        args["question"], args["evidence"]
    ),
}


def eval_value(expr: Any, env: dict[str, Any]) -> Any:
    if isinstance(expr, str) and expr.startswith("$"):
        parts = expr[1:].split(".")
        current: Any = env
        for part in parts:
            current = current[part]
        return current
    if isinstance(expr, dict):
        return {key: eval_value(value, env) for key, value in expr.items()}
    return expr


def assign_path(path: str, env: dict[str, Any], value: Any) -> None:
    if not path.startswith("$"):
        raise ValueError("output path must start with '$'")
    parts = path[1:].split(".")
    current: Any = env
    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], dict):
            current[part] = {}
        current = current[part]
    current[parts[-1]] = value


def render_by_mode(
    mode: str,
    gate_level: int,
    base_md: str,
    norm: dict[str, Any],
    matrix: list[dict[str, str]],
    template: str,
) -> str:
    if template == "compact" or mode == "reference":
        return base_md
    if mode == "digest":
        targets = norm.get("targets") or []
        bullets = [
            f"- 核心问题：{norm.get('raw')}",
            f"- 目标对象：{', '.join(targets) if targets else '未显式识别'}",
            "- 结论：execution-first 更适合闭域可枚举入口；开放域仍需要检索路径",
        ]
        return "\n".join([base_md, "\n## Digest (结构化摘要)", "\n".join(bullets)])
    if mode == "transform":
        steps = ["normalize-question", "build-comparison-axes", "contrast-matrix", "compose-answer-md"]
        return "\n".join(
            [
                base_md,
                "\n## Transform (可执行草案)",
                "### Proposed playbook",
                "```yaml\n---\nname: compare-frameworks\nmetadata:\n  kind: playbook\n  intent: compare_frameworks\n  steps:\n"
                + "\n".join([f"    - call: {step}" for step in steps])
                + "\n---\n```",
                "### Proposed procedures",
                "- normalize-question: 结构化问题意图与对象\n- build-comparison-axes: 生成对比维度\n- contrast-matrix: 生成对比矩阵\n- compose-answer-md: 组织输出文档",
            ]
        )
    if mode == "evolve":
        checklist = [
            "- 结构正确：playbook/procedure schema 校验",
            "- 引用完整：关键结论可回溯",
            "- 内容瘦身：避免冗长描述",
            "- 可回滚：变更可撤销",
        ]
        return "\n".join(
            [
                base_md,
                "\n## Evolve (变更提案草稿)",
                "### Proposal",
                "- 新增 playbook: compare-frameworks",
                "- 新增 procedures: normalize-question / build-comparison-axes / contrast-matrix / compose-answer-md",
                f"- Gate level: {gate_level}",
                "### Gate checklist",
                "\n".join(checklist),
            ]
        )
    return base_md


@dataclass
class RunResult:
    rendered: str
    settings: Settings
    proposal_path: Path | None = None


class PlaybookRuntime:
    def __init__(self, repo: Path):
        self.repo = repo
        self.skill_registry = SkillRegistry.load(repo)

    def run(
        self,
        intent: str,
        question: str = "",
        doc: str | None = None,
        settings_arg: str | Path | None = None,
        write_side_effects: bool = True,
    ) -> RunResult:
        if not question and not doc:
            raise SystemExit("Either --question or --doc must be provided.")
        settings = load_settings(self.repo, settings_arg)
        playbook = self.skill_registry.pick_playbook(intent)
        env: dict[str, Any] = {
            "settings": settings.model_dump(),
            "repo": str(self.repo),
            "inputs": {"question": question, "doc_path": doc},
            "ctx": {},
            "outputs": {},
        }
        for idx, step in enumerate(playbook.steps):
            call = step["call"]
            skill = self.skill_registry.assets.get(call)
            if not skill or skill.kind != "procedure":
                raise SystemExit(f"Invalid step {idx}: unknown procedure skill '{call}'")
            if call not in PROC_IMPL:
                raise SystemExit(f"No implementation for procedure '{call}'. Add to PROC_IMPL")
            result = PROC_IMPL[call](env, eval_value(step.get("in") or {}, env))
            if step.get("out"):
                assign_path(step["out"], env, result)

        base_md = env["outputs"].get("answer_md", "")
        if not base_md and env["outputs"].get("skill_md"):
            return RunResult(rendered=env["outputs"]["skill_md"], settings=settings)

        norm = env.get("ctx", {}).get("norm", {})
        matrix = env.get("ctx", {}).get("matrix", [])
        rendered = render_by_mode(
            settings.knowledge_mode,
            settings.gate_level,
            base_md,
            norm,
            matrix,
            settings.output_template,
        )
        if not rendered:
            rendered = env["outputs"].get("skill_md", "") or env["outputs"].get("knowledge_md", "")

        proposal_path = None
        if write_side_effects and settings.knowledge_mode == "evolve":
            proposals_dir = self.repo / "outputs" / "proposals"
            proposals_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            proposal_path = proposals_dir / f"{ts}_{intent.replace('/', '_')}.md"
            proposal_path.write_text(rendered, encoding="utf-8")

        if write_side_effects:
            self._record_usage(playbook.name, intent, question, settings.knowledge_mode)
            append_kb_log(self.repo, "run", f"{intent} in {settings.knowledge_mode} mode")

        return RunResult(rendered=rendered, settings=settings, proposal_path=proposal_path)

    def _record_usage(self, playbook_name: str, intent: str, question: str, mode: str) -> None:
        try:
            usage_dir = self.repo / "kb" / "usage"
            usage_dir.mkdir(parents=True, exist_ok=True)
            usage_path = usage_dir / f"{playbook_name}.md"
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            if usage_path.exists():
                text = usage_path.read_text(encoding="utf-8")
                if "updated_at:" in text:
                    text = re.sub(r"updated_at: .*", f"updated_at: {today}", text)
                usage_path.write_text(text, encoding="utf-8")
            events_dir = self.repo / "outputs" / "usage"
            events_dir.mkdir(parents=True, exist_ok=True)
            with (events_dir / "events.log").open("a", encoding="utf-8") as handle:
                handle.write(f"{today}\t{intent}\t{mode}\n")
        except Exception:
            pass


def compose_knowledge_from_doc(doc: str) -> tuple[str, str]:
    knowledge_md = compose_knowledge_md(extract_outline(doc))
    name = parse_frontmatter(knowledge_md).frontmatter.get("name")
    return str(name), knowledge_md
