#!/usr/bin/env python3
"""Reliability check: pass@1 and pass@k over repeated sampled answers.

Each question is answered n times per system at a non-zero temperature, each
sample is judged 0-2, and pass@k uses the unbiased estimator
1 - C(n-c, k) / C(n, k). pass^k is the all-pass reliability C(c, k) / C(n, k).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent / "real-validation"
sys.path.insert(0, str(BENCH))

import run_benchmark as rb  # noqa: E402


def answer_sampled(question: str, evidence: str, temperature: float) -> str:
    user = f"问题：{question}\n\n证据：\n{evidence}\n\n请给出回答。"
    payload = rb.chat([{"role": "system", "content": rb.ANSWER_SYSTEM},
                       {"role": "user", "content": user}], temperature=temperature)
    return rb.text_of(payload).strip()


def pass_at_k(n: int, c: int, k: int) -> float:
    if k > n:
        return float("nan")
    if c == 0:
        return 0.0
    if n - c < k:
        return 1.0
    return 1.0 - math.comb(n - c, k) / math.comb(n, k)


def pass_pow_k(n: int, c: int, k: int) -> float:
    if k > n:
        return float("nan")
    if c < k:
        return 0.0
    return math.comb(c, k) / math.comb(n, k)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=5)
    parser.add_argument("--max-k", type=int, default=5)
    parser.add_argument("--temperature", type=float, default=0.8)
    parser.add_argument("--systems", default="bm25_rag,kb_evidence")
    parser.add_argument("--out", default=str(HERE / "results"))
    args = parser.parse_args()

    questions = [json.loads(line) for line in
                 (BENCH / "questions.jsonl").read_text().splitlines() if line.strip()]
    docs = rb.load_corpus()
    chunks = rb.chunk_docs(docs)
    bm25 = rb.BM25(chunks)
    full_context = "\n\n".join(f"[{doc_id}]\n{text}" for doc_id, text in docs)
    systems = [name.strip() for name in args.systems.split(",") if name.strip()]

    records = []
    for q in questions:
        evidence_by_system = {
            "long_context": full_context[:60000],
            "bm25_rag": rb.render_evidence([{"id": c["id"], "text": c["text"]}
                                            for c in bm25.rank(q["question"])]),
            "kb_evidence": rb.render_evidence(rb.kb_evidence(q["question"])),
        }
        for system in systems:
            passes = 0
            scores = []
            for sample in range(args.samples):
                started = time.time()
                try:
                    candidate = answer_sampled(q["question"], evidence_by_system[system], args.temperature)
                except Exception as exc:  # noqa: BLE001
                    candidate = ""
                    print(f"  {q['id']} {system} sample {sample} error: {exc}", flush=True)
                judged = rb.judge(q["question"], q["gold"], candidate, q.get("answerable", True))
                scores.append(judged["score"])
                if judged["score"] == 2:
                    passes += 1
                records.append({"id": q["id"], "system": system, "sample": sample,
                                 "score": judged["score"], "answer": candidate,
                                 "latency_s": round(time.time() - started, 2)})
            print(f"{q['id']} {system}: {passes}/{args.samples} passed (scores={scores})", flush=True)

    summary = {}
    for system in systems:
        rows = [r for r in records if r["system"] == system]
        per_question = {}
        for q in questions:
            qrows = [r for r in rows if r["id"] == q["id"]]
            per_question[q["id"]] = sum(1 for r in qrows if r["score"] == 2)
        n = args.samples
        entry = {"samples": n, "pass_at": {}, "pass_pow": {}}
        for k in range(1, args.max_k + 1):
            entry["pass_at"][str(k)] = round(
                sum(pass_at_k(n, c, k) for c in per_question.values()) / len(per_question), 3)
            entry["pass_pow"][str(k)] = round(
                sum(pass_pow_k(n, c, k) for c in per_question.values()) / len(per_question), 3)
        entry["per_question_passes"] = per_question
        entry["mean_score"] = round(sum(r["score"] for r in rows) / max(1, len(rows)), 3)
        summary[system] = entry

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    outdir = Path(args.out) / stamp
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "records.json").write_text(json.dumps(records, ensure_ascii=False, indent=2))
    (outdir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))

    lines = ["# pass@1 and pass@k", "", f"samples per question: {n}, temperature: {args.temperature}", ""]
    lines.append("| system | pass@1 | pass@2 | pass@3 | pass@5 | pass^1 | pass^3 | pass^5 | mean score |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for system, entry in summary.items():
        pa = entry["pass_at"]; pp = entry["pass_pow"]
        lines.append(f"| {system} | {pa['1']} | {pa.get('2','')} | {pa.get('3','')} | {pa.get('5','')} | "
                     f"{pp['1']} | {pp.get('3','')} | {pp.get('5','')} | {entry['mean_score']} |")
    lines.extend(["", "pass@k = chance at least one of k samples is fully correct; pass^k = chance all k are.",
                  "Per-question passes are in summary.json."])
    (outdir / "REPORT.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("results:", outdir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
