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
    allowed_modes = {"reference", "digest", "transform","evolve"}
    mode = settings.get("knowledge_mode")
    if mode not in allowed_modes:
        raise SystemExit(f"Invalid knowledge_mode: {mode}.Allowed: {sorted(allowed_modes)}")
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


PROC_IMPL = {
    "normalize-question": lambda env, args: normalize_question(args["question"]),
    "build-comparison-axes": lambda env, args: build_comparison_axes(args["norm"]),
    "contrast-matrix": lambda env, args: contrast_matrix(args["norm"], args["axes"]),
    "compose-answer-md": lambda env, args: compose_answer_md(args["norm"], args["matrix"]),
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--intent", required=True)
    ap.add_argument("--question", required=True)
    ap.add_argument("--settings", default=None, help="Path to settings YAML (e.g. settings/default.yaml)")
    args = ap.parse_args()

    repo = Path(__file__).resolve().parents[1]
    settings = load_settings(repo, args.settings)

    print(f"[settings] knowledge_mode={settings.get('knowledge_mode')} gate_level={settings.get('gate_level')} auto_evolve={settings.get('auto_evolve')}")

    skills = load_skills(repo)
    pb_name = pick_playbook(skills, args.intent)
    steps = skills[pb_name]["metadata"].get("steps") or []

    env: Dict[str, Any] = {
        "settings": settings,
        "inputs": {"question": args.question},
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

    print(env["outputs"].get("answer_md", ""))


if __name__ == "__main__":
    main()
