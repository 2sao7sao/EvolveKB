#!/usr/bin/env python3
"""Pilot evaluation: real corpus, three context strategies, one model.

Run:  python experiments/real-validation/run_benchmark.py
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys
import time
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
API_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-flash"
KEY_PATH = Path.home() / ".config/evolve-memory/deepseek.key"


def api_key() -> str:
    return KEY_PATH.read_text().strip()


def chat(messages: list[dict], temperature: float = 0.1, max_tokens: int = 900) -> dict:
    body = json.dumps({"model": MODEL, "messages": messages,
                       "temperature": temperature, "max_tokens": max_tokens}).encode()
    req = urllib.request.Request(API_URL, data=body, method="POST", headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer " + api_key(),
    })
    with urllib.request.urlopen(req, timeout=180) as resp:
        payload = json.loads(resp.read())
    return payload


def text_of(payload: dict) -> str:
    return payload["choices"][0]["message"]["content"]


def tokenize(text: str) -> list[str]:
    text = text.lower()
    latin = re.findall(r"[a-z0-9_]+", text)
    grams: list[str] = []
    for run in re.findall(r"[\u4e00-\u9fff]+", text):
        grams.extend(run[i:i + 2] for i in range(max(1, len(run) - 1)))
    return latin + grams


def load_corpus() -> list[tuple[str, str]]:
    docs = []
    readme = ROOT / "README.md"
    if readme.exists():
        docs.append(("README.md", readme.read_text(encoding="utf-8")))
    for path in sorted((ROOT / "docs").glob("*.md")):
        docs.append((f"docs/{path.name}", path.read_text(encoding="utf-8")))
    return docs


def chunk_docs(docs: list[tuple[str, str]], max_chars: int = 900) -> list[dict]:
    chunks = []
    for doc_id, text in docs:
        sections = re.split(r"(?m)^(?=#{1,3} )", text)
        for section in sections:
            section = section.strip()
            if not section:
                continue
            heading = section.splitlines()[0].lstrip("# ").strip() if section.startswith("#") else "intro"
            for offset in range(0, len(section), max_chars):
                body = section[offset:offset + max_chars]
                chunks.append({"doc": doc_id, "heading": heading, "text": body})
    for idx, chunk in enumerate(chunks):
        chunk["id"] = f"{chunk['doc']}#{idx}"
    return chunks


class BM25:
    def __init__(self, chunks: list[dict], k1: float = 1.5, b: float = 0.75):
        self.chunks = chunks
        self.k1, self.b = k1, b
        self.docs = [tokenize(c["text"]) for c in chunks]
        self.avg = sum(len(d) for d in self.docs) / max(1, len(self.docs))
        self.df = Counter(t for d in self.docs for t in set(d))

    def rank(self, query: str, k: int = 4) -> list[dict]:
        terms = tokenize(query)
        n = len(self.docs)
        scored = []
        for i, doc in enumerate(self.docs):
            tf = Counter(doc)
            score = 0.0
            for term in terms:
                if term not in tf:
                    continue
                idf = math.log(1 + (n - self.df[term] + 0.5) / (self.df[term] + 0.5))
                denom = tf[term] + self.k1 * (1 - self.b + self.b * len(doc) / max(1, self.avg))
                score += idf * tf[term] * (self.k1 + 1) / max(denom, 1e-9)
            if score > 0:
                scored.append((score, i))
        scored.sort(reverse=True)
        return [self.chunks[i] for _, i in scored[:k]]


def kb_evidence(question: str, k: int = 4) -> list[dict]:
    kb_root = Path(os.environ.get("EVOLVEKB_KB_ROOT", str(ROOT)))
    proc = subprocess.run(
        [sys.executable, "-m", "evolvekb.cli", "query", question,
         "--retriever", "bm25", "--limit", str(k), "--json"],
        cwd=kb_root, capture_output=True, text=True, timeout=120)
    if proc.returncode != 0:
        return []
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return []
    return payload.get("items", [])


ANSWER_SYSTEM = (
    "你是知识库问答助手。只允许使用「证据」中的内容回答，不要使用你自己的先验知识补充事实。"
    "如果证据不足以回答，直接输出「无法回答」并说明缺少什么。"
    "引用格式：在相关句末标注证据编号，例如 [docs/RETRIEVAL.md#3]。"
    "回答用中文，简洁，不要复述问题。"
)


def render_evidence(items: list[dict]) -> str:
    lines = []
    for idx, item in enumerate(items, 1):
        label = item.get("id") or item.get("source_ref") or item.get("name") or f"e{idx}"
        text = (item.get("text") or "").strip()
        lines.append(f"[{label}] {text}")
    return "\n\n".join(lines)


def answer(question: str, evidence: str) -> str:
    user = f"问题：{question}\n\n证据：\n{evidence}\n\n请给出回答。"
    payload = chat([{"role": "system", "content": ANSWER_SYSTEM},
                    {"role": "user", "content": user}])
    return text_of(payload).strip()


JUDGE_SYSTEM = (
    "你是严格的事实评审。给定「问题」「参考答案」「候选回答」，判断候选回答是否正确。"
    "只输出 JSON，不要输出其他内容。格式："
    '{"score": 0, "reason": "", "fabricated": false}'
    "。score 取值：2=事实与参考答案一致且无虚构；1=部分正确但缺少关键事实；0=错误、矛盾、答非所问或本应回答无法回答却编造。"
    "fabricated=true 表示候选回答给出了证据/参考答案中没有的事实。"
)


def judge(question: str, gold: str, candidate: str, answerable: bool) -> dict:
    user = (f"问题：{question}\n参考答案：{gold}\n"
            f"该问题在语料中{'有答案' if answerable else '没有答案（应回答无法回答）'}。\n"
            f"候选回答：{candidate}")
    payload = chat([{"role": "system", "content": JUDGE_SYSTEM},
                    {"role": "user", "content": user}], temperature=0.0, max_tokens=300)
    raw = text_of(payload)
    match = re.search(r"\{.*\}", raw, re.S)
    if not match:
        return {"score": 1, "reason": "judge_unparseable", "fabricated": False}
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return {"score": 1, "reason": "judge_invalid_json", "fabricated": False}
    return {"score": int(data.get("score", 1)), "reason": str(data.get("reason", ""))[:300],
            "fabricated": bool(data.get("fabricated", False))}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(HERE / "results"))
    parser.add_argument("--systems", default="long_context,bm25_rag,kb_evidence")
    parser.add_argument("--tag", default="")
    args = parser.parse_args()
    wanted = {name.strip() for name in args.systems.split(",") if name.strip()}

    questions = [json.loads(line) for line in (HERE / "questions.jsonl").read_text().splitlines() if line.strip()]
    docs = load_corpus()
    chunks = chunk_docs(docs)
    bm25 = BM25(chunks)
    full_context = "\n\n".join(f"[{doc_id}]\n{text}" for doc_id, text in docs)

    records = []
    for q in questions:
        strategies = {
            "long_context": full_context[:60000],
            "bm25_rag": render_evidence(
                [{"id": c["id"], "text": c["text"]} for c in bm25.rank(q["question"])]),
            "kb_evidence": render_evidence(kb_evidence(q["question"])),
        }
        for name, evidence in strategies.items():
            if name not in wanted:
                continue
            started = time.time()
            try:
                candidate = answer(q["question"], evidence)
                error = None
            except Exception as exc:  # noqa: BLE001 - record and continue
                candidate, error = "", str(exc)
            judged = judge(q["question"], q["gold"], candidate, q.get("answerable", True)) if candidate else {
                "score": 0, "reason": error or "empty_answer", "fabricated": False}
            cited = [d for d in q.get("gold_docs", []) if d and d in candidate]
            records.append({
                "id": q["id"], "type": q["type"], "system": name, "question": q["question"],
                "gold_docs": q.get("gold_docs", []), "answerable": q.get("answerable", True),
                "evidence_chars": len(evidence), "answer": candidate,
                "score": judged["score"], "judge_reason": judged["reason"],
                "fabricated": judged["fabricated"], "gold_doc_cited": bool(cited),
                "latency_s": round(time.time() - started, 2), "error": error,
            })
            print(f"{q['id']} {name}: score={judged['score']} cited={bool(cited)} "
                  f"chars={len(evidence)}", flush=True)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + (f"-{args.tag}" if args.tag else "")
    outdir = Path(args.out) / stamp
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "records.json").write_text(json.dumps(records, ensure_ascii=False, indent=2))

    summary = {}
    for system in ("long_context", "bm25_rag", "kb_evidence"):
        rows = [r for r in records if r["system"] == system]
        summary[system] = {
            "questions": len(rows),
            "mean_score": round(sum(r["score"] for r in rows) / max(1, len(rows)), 3),
            "exact_rate": round(sum(1 for r in rows if r["score"] == 2) / max(1, len(rows)), 3),
            "gold_cited_rate": round(sum(1 for r in rows if r["gold_doc_cited"]) / max(1, len(rows)), 3),
            "fabricated_rate": round(sum(1 for r in rows if r["fabricated"]) / max(1, len(rows)), 3),
            "mean_evidence_chars": round(sum(r["evidence_chars"] for r in rows) / max(1, len(rows))),
        }
    unanswerable = [r for r in records if r["type"] == "unanswerable"]
    summary["unanswerable_refusal"] = {
        r["system"]: ("refused" if r["score"] == 2 else "failed") for r in unanswerable
    }
    (outdir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("results:", outdir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
