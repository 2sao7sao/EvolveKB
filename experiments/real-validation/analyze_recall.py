
import json, os, subprocess, sys, re
from pathlib import Path
ROOT = Path("/Users/7sao/Downloads/github清理/repos/EvolveKB")
KB = Path("/tmp/evolvekb-real")
qs = [json.loads(l) for l in (ROOT/"experiments/real-validation/questions.jsonl").read_text().splitlines() if l.strip()]

def stem(doc):
    return Path(doc).stem.lower().replace("_","-")

def hit(labels, gold_docs):
    if not gold_docs:
        return None
    for g in gold_docs:
        s = stem(g)
        for lab in labels:
            if s and s in lab.lower().replace("_","-"):
                return True
    return False

def kb_items(q):
    out = subprocess.run([sys.executable,"-m","evolvekb.cli","query",q,"--retriever","bm25","--limit","4","--json"],
                         cwd=KB, capture_output=True, text=True)
    if out.returncode != 0: return []
    try: return json.loads(out.stdout).get("items",[])
    except Exception: return []

# independent bm25 (reuse benchmark module)
sys.path.insert(0, str(ROOT/"experiments/real-validation"))
import run_benchmark as rb
docs = rb.load_corpus()
chunks = rb.chunk_docs(docs)
bm25 = rb.BM25(chunks)

rows = []
for q in qs:
    items = kb_items(q["question"])
    kb_labels = [str(i.get("source_ref") or i.get("name") or "") for i in items]
    bm_top = bm25.rank(q["question"], 4)
    bm_docs = [c["doc"] for c in bm_top]
    rows.append({
        "id": q["id"], "type": q["type"], "gold_docs": q["gold_docs"],
        "kb_recall_at4": hit(kb_labels, q["gold_docs"]),
        "kb_item_count": len(items),
        "bm25_recall_at4": hit(bm_docs, q["gold_docs"]),
        "bm25_docs": bm_docs,
    })

def rate(key):
    vals = [r[key] for r in rows if r[key] is not None]
    return f"{sum(1 for v in vals if v)}/{len(vals)}"

print("q   kb_recall@4  bm25_recall@4")
for r in rows:
    print(f"{r['id']}  {str(r['kb_recall_at4']):5}  {str(r['bm25_recall_at4']):5}  bm25={r['bm25_docs']}")
print("KB recall@4 :", rate("kb_recall_at4"))
print("BM25 recall@4:", rate("bm25_recall_at4"))
print("KB 平均命中条数:", round(sum(r["kb_item_count"] for r in rows)/len(rows),1))
