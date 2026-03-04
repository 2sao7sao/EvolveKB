#!/usr/bin/env python3
"""
scripts/run.py

Execution engine (MVP):
- Select a playbook-skill by `--intent` (maps to skill name or metadata.intent)
- Execute metadata.steps (call procedure-skills)
- Deterministic placeholder implementations included; replace with LLM/tool calls later.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import yaml

from frontmatter import read_skill_md


def load_skills(repo: Path) -> Dict[str, Dict[str, Any]]:
    skills_root = repo / "skills"
    skills: Dict[str, Dict[str, Any]] = {}
    if not skills_root.exists():
        return skills

    for d in skills_root.iterdir():
        if d.is_dir() and (d / "SKILL.md").exists():
            doc = read_skill_md(d)
            fm = doc.frontmatter
            md = fm.get("metadata") or {}
            kind = str(md.get("kind") or "other")
            skills[fm["name"]] = {
                "frontmatter": fm,
                "metadata": md,
                "kind": kind,
                "dir": d,
            }
    return skills


def pick_playbook(skills: Dict[str, Dict[str, Any]], intent: str) -> str:
    # Prefer exact skill name match
    if intent in skills and skills[intent]["kind"] == "playbook":
        return intent

    # Else find by metadata.intent
    for name, s in skills.items():
        if s["kind"] != "playbook":
            continue
        if str(s["metadata"].get("intent") or "").strip() == intent:
            return name

    raise KeyError(f"No playbook for intent: {intent}")


def load_settings(repo: Path, settings_arg: Optional[str]) -> Dict[str, Any]:
    # Safe defaults (so settings is optional)
    settings: Dict[str, Any] = {
        "knowledge_mode": "reference",
        "gate_level": 1,
        "auto_evolve": False,
        "max_skill_md_bytes": 50000,
        "output_template": "expanded",
    }
    if not settings_arg:
        return settings

    p = Path(settings_arg)
    if not p.is_absolute():
        p = repo / p

    if not p.exists():
        raise SystemExit(f"Settings file not found: {p}")

    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise SystemExit("Settings YAML must be a mapping/dict at top level")

    settings.update(data)
# --- basic settings validation (PR #4) ---
    allowed_modes = {"reference", "digest", "transform", "evolve"}
    mode = settings.get("knowledge_mode")
    if mode not in allowed_modes:
        raise SystemExit(f"Invalid knowledge_mode: {mode}.Allowed: {sorted(allowed_modes)}")
    allowed_templates = {"compact", "expanded"}
    template = settings.get("output_template")
    if template not in allowed_templates:
        raise SystemExit(f"Invalid output_template: {template}. Allowed: {sorted(allowed_templates)}")
    try:
        gate = int(settings.get("gate_level"))
    except Exception:
        raise SystemExit(f"Invalid gate_level: {settings.get('gate_level')} (must be int 0..3)")
    if gate < 0 or gate > 3:
        raise SystemExit(f"Invalid gate_level: {gate} (must be int 0..3)")
    settings["gate_level"] = gate
    return settings


# --- Deterministic procedure implementations (MVP placeholders) ---
def normalize_question(question: str) -> Dict[str, Any]:
    targets = []
    for token in [
        "graphrag",
        "rag",
        "md",
        "knowledge",
        "skills",
        "mcp",
        "function call",
        "openclaw",
    ]:
        if token.lower() in question.lower():
            targets.append(token)
    intent_hint = "compare_frameworks" if ("对比" in question or "compare" in question.lower()) else "unknown"
    return {"intent_hint": intent_hint, "targets": targets, "constraints": [], "raw": question}


def build_comparison_axes(norm: Dict[str, Any]) -> List[Dict[str, str]]:
    return [
        {"axis": "index_time_synthesis", "why_matters": "建库阶段是否先综合/抽象"},
        {"axis": "query_time_cost", "why_matters": "查询时成本/延迟/稳定性"},
        {"axis": "governance", "why_matters": "可审计、可回滚、防漂移"},
        {"axis": "multi_hop", "why_matters": "多跳路径是否稳定可解释"},
        {"axis": "maintenance", "why_matters": "维护复杂度转移（索引结构 vs 知识工程）"},
    ]


def contrast_matrix(norm: Dict[str, Any], axes: List[Dict[str, str]]) -> List[Dict[str, str]]:
    A = "GraphRAG / graph-based RAG"
    B = "MD Knowledge (skills→knowledge, execution-first)"
    out: List[Dict[str, str]] = []

    for a in axes:
        axis = a["axis"]
        if axis == "index_time_synthesis":
            out.append(
                {"axis": axis, "A": "抽实体/关系 + 社区摘要", "B": "编译为可调用procedures/playbooks", "tradeoff": "两者都前置综合；B强调执行语义与治理"}
            )
        elif axis == "query_time_cost":
            out.append({"axis": axis, "A": "检索/遍历/拼上下文", "B": "入口→步骤执行，更稳定", "tradeoff": "A更灵活；B要求入口覆盖"})
        elif axis == "governance":
            out.append({"axis": axis, "A": "索引管线治理为主", "B": "Git/PR+Gate，知识资产一等公民", "tradeoff": "B更适合工程迭代"})
        elif axis == "multi_hop":
            out.append({"axis": axis, "A": "图结构辅助证据连接", "B": "playbook显式编排多步", "tradeoff": "B路径稳定，但需要维护契约"})
        else:
            out.append({"axis": axis, "A": "图/索引维护", "B": "知识模块/门控维护", "tradeoff": "复杂度转移"})
    return out


def compose_answer_md(norm: Dict[str, Any], matrix: List[Dict[str, str]]) -> str:
    lines: List[str] = []
    lines.append("# 对比：GraphRAG vs Execution-first Markdown Knowledge\n")
    lines.append("你选择的是 **执行式知识编译**：用 procedures/playbooks 取代“检索碎片”。\n")
    lines.append("| 维度 | GraphRAG | Execution-first MD | 权衡 |")
    lines.append("|---|---|---|---|")
    for r in matrix:
        lines.append(f"| {r['axis']} | {r['A']} | {r['B']} | {r['tradeoff']} |")
    lines.append("\n## 建议\n- 闭域可枚举入口：execution-first 更稳。\n- 开放域入口不可枚举：GraphRAG 弹性更强。")
    return "\n".join(lines)

def extract_outline(doc_path: str) -> Dict[str, Any]:
    p = Path(doc_path)
    if not p.exists():
        raise SystemExit(f"Document not found: {doc_path}")
    text = p.read_text(encoding="utf-8", errors="ignore")
    lines = [ln.rstrip() for ln in text.splitlines()]
    headings: List[Dict[str, Any]] = []
    for ln in lines:
        if ln.startswith("#"):
            level = len(ln) - len(ln.lstrip("#"))
            title = ln.lstrip("#").strip()
            if title:
                headings.append({"level": level, "title": title})

    summary = ""
    buf: List[str] = []
    for ln in lines:
        if ln.strip() == "":
            if buf:
                summary = " ".join(buf).strip()
                break
            continue
        if not ln.startswith("#") and not ln.lstrip().startswith("<"):
            buf.append(ln.strip())
    if not summary and buf:
        summary = " ".join(buf).strip()

    return {"headings": headings, "summary": summary, "doc_name": p.stem, "doc_path": str(p)}

def compose_skill_draft(outline: Dict[str, Any]) -> str:
    doc_name = outline.get("doc_name") or "doc"
    name = f"ingest-{doc_name}".lower().replace("_", "-").replace(" ", "-")
    headings = outline.get("headings") or []
    summary = outline.get("summary") or ""

    body_lines = [f"# {name} (procedure)", "", "## Summary", summary or "N/A", "", "## Outline"]
    if headings:
        for h in headings:
            indent = "  " * max(0, int(h.get("level", 1)) - 1)
            body_lines.append(f"{indent}- {h.get('title')}")
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

def compose_knowledge_md(outline: Dict[str, Any]) -> str:
    doc_name = outline.get("doc_name") or "doc"
    doc_path = outline.get("doc_path") or doc_name
    name = f"{doc_name}".lower().replace("_", "-").replace(" ", "-")
    headings = outline.get("headings") or []
    summary = outline.get("summary") or ""
    concepts = [h.get("title") for h in headings[:8] if h.get("title")]  # top headings as concepts
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    fm_dict = {
        "name": name,
        "kind": "knowledge",
        "source": doc_path,
        "summary": summary or "N/A",
        "concepts": concepts,
        "updated_at": today,
    }
    fm_yaml = yaml.safe_dump(fm_dict, sort_keys=False, allow_unicode=True).strip()
    fm = ["---", fm_yaml, "---", ""]
    body = [
        f"# {doc_name}",
        "",
        "## Notes",
        summary or "N/A",
    ]
    return "\n".join(fm + body) + "\n"

PROC_IMPL = {
    "normalize-question": lambda env, args: normalize_question(args["question"]),
    "build-comparison-axes": lambda env, args: build_comparison_axes(args["norm"]),
    "contrast-matrix": lambda env, args: contrast_matrix(args["norm"], args["axes"]),
    "compose-answer-md": lambda env, args: compose_answer_md(args["norm"], args["matrix"]),
    "extract-outline": lambda env, args: extract_outline(args["doc_path"]),
    "compose-skill-draft": lambda env, args: compose_skill_draft(args["outline"]),
    "compose-knowledge-md": lambda env, args: compose_knowledge_md(args["outline"]),
}


def eval_value(expr: Any, env: Dict[str, Any]) -> Any:
    if isinstance(expr, str) and expr.startswith("$"):
        parts = expr[1:].split(".")
        cur: Any = env
        for p in parts:
            cur = cur[p]
        return cur
    if isinstance(expr, dict):
        return {k: eval_value(v, env) for k, v in expr.items()}
    return expr


def assign_path(path: str, env: Dict[str, Any], value: Any):
    assert path.startswith("$")
    parts = path[1:].split(".")
    cur: Any = env
    for p in parts[:-1]:
        if p not in cur or not isinstance(cur[p], dict):
            cur[p] = {}
        cur = cur[p]
    cur[parts[-1]] = value


def render_by_mode(mode: str, gate_level: int, base_md: str, norm: Dict[str, Any], matrix: List[Dict[str, str]], template: str) -> str:
    if template == "compact":
        return base_md

    if mode == "reference":
        return base_md

    if mode == "digest":
        targets = norm.get("targets") or []
        bullets = [
            f"- 核心问题：{norm.get('raw')}",
            f"- 目标对象：{', '.join(targets) if targets else '未显式识别'}",
            f"- 结论：execution-first 更适合闭域可枚举入口；开放域仍需要检索路径",
        ]
        return "\n".join(
            [
                base_md,
                "\n## Digest (结构化摘要)",
                "\n".join(bullets),
            ]
        )

    if mode == "transform":
        steps = [
            "normalize-question",
            "build-comparison-axes",
            "contrast-matrix",
            "compose-answer-md",
        ]
        return "\n".join(
            [
                base_md,
                "\n## Transform (可执行草案)",
                "### Proposed playbook",
                "```yaml\n---\nname: compare-frameworks\nmetadata:\n  kind: playbook\n  intent: compare_frameworks\n  steps:\n"
                + "\n".join([f"    - call: {s}" for s in steps])
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--intent", required=True)
    ap.add_argument("--question", default="")
    ap.add_argument("--doc", default=None, help="Path to a document for ingestion workflows")
    ap.add_argument("--settings", default=None, help="Path to settings YAML (e.g. settings/default.yaml)")
    args = ap.parse_args()
    if not args.question and not args.doc:
        raise SystemExit("Either --question or --doc must be provided.")

    repo = Path(__file__).resolve().parents[1]
    settings = load_settings(repo, args.settings)

    print(f"[settings] knowledge_mode={settings.get('knowledge_mode')} gate_level={settings.get('gate_level')} auto_evolve={settings.get('auto_evolve')}")

    skills = load_skills(repo)
    pb_name = pick_playbook(skills, args.intent)
    steps = skills[pb_name]["metadata"].get("steps") or []

    env: Dict[str, Any] = {
        "settings": settings,
        "inputs": {"question": args.question, "doc_path": args.doc},
        "ctx": {},
        "outputs": {},
    }

    for idx, st in enumerate(steps):
        call = st["call"]  # existing schema
        if call not in skills or skills[call]["kind"] != "procedure":
            raise SystemExit(f"Invalid step {idx}: unknown procedure skill '{call}'")

        call_args = eval_value(st.get("in") or {}, env)

        if call not in PROC_IMPL:
            raise SystemExit(
                f"No implementation for procedure '{call}'. Add to PROC_IMPL in scripts/run.py"
            )

        result = PROC_IMPL[call](env, call_args)

        out_path = st.get("out")
        if out_path:
            assign_path(out_path, env, result)

    base_md = env["outputs"].get("answer_md", "")
    if not base_md and env["outputs"].get("skill_md"):
        print(env["outputs"]["skill_md"])
        return
    norm = env.get("ctx", {}).get("norm", {})
    matrix = env.get("ctx", {}).get("matrix", [])
    mode = settings.get("knowledge_mode", "reference")
    gate = int(settings.get("gate_level", 1))
    template = settings.get("output_template", "expanded")
    rendered = render_by_mode(mode, gate, base_md, norm, matrix, template)

    if mode == "evolve":
        proposals_dir = repo / "outputs" / "proposals"
        proposals_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        intent = args.intent.replace("/", "_")
        proposal_path = proposals_dir / f"{ts}_{intent}.md"
        proposal_path.write_text(rendered, encoding="utf-8")
        print(f"[proposal] {proposal_path}")

    if not rendered:
        rendered = env["outputs"].get("skill_md", "") or env["outputs"].get("knowledge_md", "")
    print(rendered)


if __name__ == "__main__":
    main()
